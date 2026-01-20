/**
 * Proof of Concept: LanceDB vector storage and search
 * Validates: @lancedb/lancedb package works, can create tables and search
 */

import * as lancedb from '@lancedb/lancedb';
import { join } from 'path';
import { mkdirSync, rmSync } from 'fs';

interface VectorData {
    id: string;
    vector: number[];
    text: string;
}

async function main() {
    const dataDir = join(process.cwd(), 'poc/data/vectors');

    // Clean start
    rmSync(dataDir, { recursive: true, force: true });
    mkdirSync(dataDir, { recursive: true });

    console.log('✓ Connecting to LanceDB...');
    const db = await lancedb.connect(dataDir);

    console.log('✓ Creating sample vectors...');
    const sampleData: VectorData[] = [
        {
            id: '1',
            vector: [0.1, 0.2, 0.3, 0.4],
            text: 'TypeScript programming',
        },
        {
            id: '2',
            vector: [0.2, 0.3, 0.4, 0.5],
            text: 'JavaScript development',
        },
        {
            id: '3',
            vector: [0.9, 0.1, 0.1, 0.1],
            text: 'Python machine learning',
        },
    ];

    console.log('✓ Creating table...');
    const table = await db.createTable('test_vectors', sampleData, {
        mode: 'overwrite',
    });

    console.log('✓ Performing vector search...');
    const query = [0.15, 0.25, 0.35, 0.45]; // Similar to first two
    const results = await table.vectorSearch(query).limit(2).toArray();

    console.log('\n  Search Results:');
    for (const result of results) {
        console.log(`  - ${result.text} (distance: ${result._distance?.toFixed(4)})`);
    }

    // Verify results are ordered by distance
    if (results.length >= 2) {
        const distances = results.map(r => r._distance ?? Infinity);
        if (distances[0] !== undefined && distances[0] <= (distances[1] ?? Infinity)) {
            console.log('\n✅ LanceDB test passed!');
        } else {
            console.error('\n❌ Results not properly ordered by distance');
            process.exit(1);
        }
    } else {
        console.error('\n❌ Expected at least 2 results');
        process.exit(1);
    }
}

main().catch(err => {
    console.error('❌ LanceDB test failed:', err);
    process.exit(1);
});
