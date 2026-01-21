import { logger } from '../utils/logger.js';

export interface WorkerStatus {
  running: boolean;
  jobs: Array<{
    id: string;
    name: string;
    next_run: string | null;
  }>;
  last_results: Record<string, unknown>;
  worker_metrics: Record<string, unknown>;
}

export interface WorkerResult {
  success: boolean;
  duration: number;
  result?: unknown;
  error?: string;
  metrics: Record<string, unknown>;
}

export class WorkerClient {
  private pythonPath: string;

  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python3';
  }

  async getStatus(): Promise<WorkerStatus | null> {
    try {
      // Workers communicate via HTTP or file-based status
      const fs = await import('fs');

      // Check if worker manager is running
      try {
        const pidFile = './data/worker_manager.pid';

        if (fs.existsSync(pidFile)) {
          return {
            running: true,
            jobs: [],
            last_results: {},
            worker_metrics: {},
          };
        }
      } catch (error) {
        logger.debug('Could not check worker status:', error);
      }

      return null;
    } catch (error) {
      logger.error('Error getting worker status:', error);
      return null;
    }
  }

  async triggerWorker(workerName: string): Promise<boolean> {
    try {
      const { spawn } = await import('child_process');

      logger.info(`Manually triggering worker: ${workerName}`);

      // Execute worker directly
      const workerScript = `./python/workers/${workerName}.py`;

      const proc = spawn(this.pythonPath, [workerScript]);

      return new Promise((resolve) => {
        proc.on('close', (code) => {
          if (code === 0) {
            logger.info(`Worker ${workerName} completed successfully`);
            resolve(true);
          } else {
            logger.error(`Worker ${workerName} failed with code ${code}`);
            resolve(false);
          }
        });
      });
    } catch (error) {
      logger.error(`Error triggering worker ${workerName}:`, error);
      return false;
    }
  }
}

export const workerClient = new WorkerClient();
