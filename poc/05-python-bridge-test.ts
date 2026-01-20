/**
 * Proof of Concept: TypeScript calling Python embedding service
 * Validates: HTTP communication works, JSON serialization correct
 */

import { spawn, ChildProcess } from 'child_process';
import { writeFileSync, unlinkSync } from 'fs';
import { join } from 'path';

const PYTHON_SERVER = `
from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/embed', methods=['POST'])
def embed():
    data = request.get_json()
    text = data.get('text', '')
    # Return a dummy embedding (384 dimensions like MiniLM)
    embedding = np.random.rand(384).tolist()
    return jsonify({'embedding': embedding, 'dimensions': 384, 'text_length': len(text)})

if __name__ == '__main__':
    print('Starting test server on port 5555...', flush=True)
    app.run(port=5555, debug=False, use_reloader=False)
`;

const SERVER_PATH = join(process.cwd(), 'poc/temp_server.py');

async function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForServer(url: string, maxAttempts = 20): Promise<boolean> {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            const response = await fetch(url);
            if (response.ok) return true;
        } catch {
            await sleep(250);
        }
    }
    return false;
}

async function main(): Promise<void> {
    let pyProcess: ChildProcess | null = null;

    try {
        // Write temporary Python server
        writeFileSync(SERVER_PATH, PYTHON_SERVER);

        console.log('✓ Starting Python test server...');
        pyProcess = spawn('python', [SERVER_PATH], {
            stdio: ['ignore', 'pipe', 'pipe'],
        });

        pyProcess.stderr?.on('data', data => {
            // Flask logs to stderr
        });

        // Wait for server to start
        console.log('  Waiting for server...');
        const serverReady = await waitForServer('http://127.0.0.1:5555/health');

        if (!serverReady) {
            throw new Error('Server failed to start within timeout');
        }

        console.log('✓ Testing HTTP communication...');

        // Test 1: Health check
        const healthResponse = await fetch('http://127.0.0.1:5555/health');
        const healthData = await healthResponse.json();
        console.log('  Health check:', healthData);

        // Test 2: Embedding generation
        const embedResponse = await fetch('http://127.0.0.1:5555/embed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: 'Test message for embedding' }),
        });

        const embedData = (await embedResponse.json()) as {
            dimensions: number;
            embedding: number[];
            text_length: number;
        };
        console.log(`  Embedding generated: ${embedData.dimensions} dimensions`);
        console.log(`  First 5 values: [${embedData.embedding.slice(0, 5).map(v => v.toFixed(4)).join(', ')}]`);
        console.log(`  Text length received: ${embedData.text_length}`);

        // Verify response structure
        if (embedData.dimensions === 384 && embedData.embedding.length === 384) {
            console.log('\n✅ TypeScript ↔ Python communication works!');
        } else {
            throw new Error('Invalid response structure');
        }
    } catch (error) {
        console.error('❌ Communication failed:', error);
        process.exit(1);
    } finally {
        if (pyProcess) {
            pyProcess.kill();
        }
        try {
            unlinkSync(SERVER_PATH);
        } catch {
            // Ignore cleanup errors
        }
    }
}

main();
