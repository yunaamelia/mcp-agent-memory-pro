import { writeFileSync, appendFileSync, existsSync } from 'fs';
import { config } from './config.js';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  private level: LogLevel;
  private logFile?: string;

  constructor(level: LogLevel = 'info', logFile?: string) {
    this.level = level;
    this.logFile = logFile;

    // Create log file if it doesn't exist
    if (this.logFile && !existsSync(this.logFile)) {
      writeFileSync(this.logFile, '');
    }
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.level];
  }

  private formatMessage(level: LogLevel, ...args: unknown[]): string {
    const timestamp = new Date().toISOString();
    const message = args
      .map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg)))
      .join(' ');
    return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
  }

  private log(level: LogLevel, ...args: unknown[]) {
    if (!this.shouldLog(level)) return;

    const formatted = this.formatMessage(level, ...args);

    // Console output
    const consoleMethod =
      level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
    consoleMethod(formatted);

    // File output
    if (this.logFile) {
      try {
        appendFileSync(this.logFile, formatted + '\n');
      } catch (error) {
        console.error('Failed to write to log file:', error);
      }
    }
  }

  debug(...args: unknown[]) {
    this.log('debug', ...args);
  }

  info(...args: unknown[]) {
    this.log('info', ...args);
  }

  warn(...args: unknown[]) {
    this.log('warn', ...args);
  }

  error(...args: unknown[]) {
    this.log('error', ...args);
  }

  setLevel(level: LogLevel) {
    this.level = level;
  }
}

export const logger = new Logger(config.logLevel, config.logFile);
