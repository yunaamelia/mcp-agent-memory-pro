export interface AppConfig {
  // Data
  dataDir: string;
  databasePath: string;
  vectorStorePath: string;

  // Embedding
  embeddingServiceUrl: string;
  embeddingModel: string;
  embeddingDimensions: number;

  // Memory
  shortTermDays: number;
  workingTermDays: number;

  // Logging
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  logFile?: string;

  // Server
  serverName: string;
  serverVersion: string;

  // Performance
  vectorSearchLimit: number;
  cacheEnabled: boolean;
}
