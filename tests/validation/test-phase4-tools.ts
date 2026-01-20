#!/usr/bin/env node

// import { handleStoreMemory } from '../../src/tools/store.js';
import { handleMemoryQuery } from '../../src/tools/memory_query.js';
import { handleMemoryExport } from '../../src/tools/memory_export.js';
import { handleMemoryHealth } from '../../src/tools/memory_health.js';
import { handleMemoryDashboard } from '../../src/tools/memory_dashboard.js';
import { initializeDatabase, closeDatabase, getDatabase } from '../../src/storage/database.js';
import { MemoryType, MemorySource } from '../../src/types/memory.js';
import fs from 'fs';
import path from 'path';

async function validatePhase4Tools() {
  console.log('🔍 Validating Phase 4 MCP Tools...\n');

  try {
    // Setup - we need some data first
    await initializeDatabase();

    // Create a test memory so queries have something to find
    console.log('Setup: Creating test memory manually...');
    const db = getDatabase();
    const now = Date.now();

    try {
      db.prepare(
        `
            INSERT INTO memories (
                id, type, source, content, project, importance_score, 
                timestamp, created_at, access_count, archived, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `
      ).run(
        'test-mem-id-1',
        MemoryType.NOTE,
        MemorySource.MANUAL,
        'Phase 4 Tool Validation Test Memory',
        'validation-phase4',
        0.9,
        now,
        now,
        0,
        0,
        'dummy_hash'
      );
      console.log('Setup: Test memory created.');
    } catch (e) {
      console.log('Setup: Could not insert memory (maybe already exists)', e);
    }

    // Test 1: Memory Query Tool (MemQL)
    console.log('\nTest 1: Memory Query Tool');
    const queryParams = {
      query: "SELECT * FROM memories WHERE project = 'validation-phase4' LIMIT 1",
    };

    const queryResult = await handleMemoryQuery(queryParams);
    const queryResponse = JSON.parse(queryResult.content[0].text);

    if (queryResponse.count === 0) {
      console.warn('  ⚠️ Query returned 0 results.');
    } else {
      console.log(`  ✓ Query tool successful (Found ${queryResponse.count} results)`);
    }

    // Test 2: Memory Export Tool
    console.log('\nTest 2: Memory Export Tool');
    const exportParams = {
      format: 'json',
      filters: { project: 'validation-phase4' },
    };

    const exportResult = await handleMemoryExport(exportParams);
    const exportResponse = JSON.parse(exportResult.content[0].text);

    if (!exportResponse.success) {
      throw new Error(`Export tool failed: ${exportResponse.error || 'Unknown error'}`);
    }

    if (exportResponse.count === undefined) {
      throw new Error('Export tool did not return count');
    }

    console.log(
      `  ✓ Export tool successful (Exported ${exportResponse.count} items to ${exportResponse.output_path})`
    );

    // Clean up export file
    if (exportResponse.output_path && fs.existsSync(exportResponse.output_path)) {
      fs.unlinkSync(exportResponse.output_path);
      console.log('    (Cleaned up export file)');
    }

    // Test 3: Memory Health Tool
    console.log('\nTest 3: Memory Health Tool');

    const healthResult = await handleMemoryHealth({ detailed: true });
    const healthResponse = JSON.parse(healthResult.content[0].text);

    if (!healthResponse.overall_status) {
      throw new Error('Health tool did not return status');
    }

    console.log(`  ✓ Health tool successful (Status: ${healthResponse.overall_status})`);

    // Test 4: Memory Dashboard Tool
    console.log('\nTest 4: Memory Dashboard Tool');

    const dashboardResult = await handleMemoryDashboard({
      sections: ['overview', 'usage'],
    });
    const dashboardResponse = JSON.parse(dashboardResult.content[0].text);

    if (!dashboardResponse.data || !dashboardResponse.data.overview) {
      throw new Error('Dashboard tool did not return expected data');
    }

    console.log(`  ✓ Dashboard tool successful`);

    console.log('\n✅ All Phase 4 tool tests passed!');
    closeDatabase();
    process.exit(0);
  } catch (error) {
    console.log('\n❌ Phase 4 tools validation failed');
    try {
      console.log('Error details:', error);
    } catch (e) {
      console.log('Error object could not be logged');
    }
    try {
      closeDatabase();
    } catch (e) {}
    process.exit(1);
  }
}

validatePhase4Tools();
