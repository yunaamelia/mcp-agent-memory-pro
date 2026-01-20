"""
Health Monitor
Real-time system health monitoring
"""

import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil


class HealthMonitor:
    """Monitors system health"""

    def __init__(self, db_connection: sqlite3.Connection, data_dir: Path):
        self.conn = db_connection
        self.data_dir = data_dir

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status"""

        return {
            'overall_status': self._calculate_overall_status(),
            'database':  self._check_database_health(),
            'storage': self._check_storage_health(),
            'memory': self._check_memory_health(),
            'workers': self._check_workers_health(),
            'timestamp': datetime.now(UTC).isoformat()
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall health status"""

        db_health = self._check_database_health()
        storage_health = self._check_storage_health()

        if db_health['status'] == 'healthy' and storage_health['status'] == 'healthy':
            return 'healthy'
        elif db_health['status'] == 'degraded' or storage_health['status'] == 'degraded':
            return 'degraded'
        else:
            return 'unhealthy'

    def _check_database_health(self) -> dict[str, Any]:
        """Check database health"""

        try:
            # Test query
            start = time.time()
            cursor = self.conn.execute('SELECT COUNT(*) FROM memories')
            count = cursor.fetchone()[0]
            query_time = time.time() - start

            # Check database size
            db_size = self._get_database_size()

            # Determine status
            status = 'healthy'
            issues = []

            if query_time > 1.0:
                status = 'degraded'
                issues. append('Slow query performance')

            if db_size > 1000 * 1024 * 1024:  # > 1GB
                issues.append('Large database size')

            return {
                'status': status,
                'memory_count': count,
                'query_time_ms': round(query_time * 1000, 2),
                'size_mb': round(db_size / (1024 * 1024), 2),
                'issues':  issues
            }

        except Exception as e:
            return {
                'status':  'unhealthy',
                'error':  str(e)
            }

    def _check_storage_health(self) -> dict[str, Any]:
        """Check storage health"""

        try:
            # Get disk usage
            disk = psutil.disk_usage(str(self.data_dir))

            status = 'healthy'
            issues = []

            if disk.percent > 90:
                status = 'unhealthy'
                issues.append('Disk usage critical')
            elif disk.percent > 80:
                status = 'degraded'
                issues.append('Disk usage high')

            return {
                'status': status,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk. used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent_used': disk.percent,
                'issues':  issues
            }

        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }

    def _check_memory_health(self) -> dict[str, Any]:
        """Check memory tier health"""

        cursor = self.conn.execute('''
            SELECT tier, COUNT(*) as count
            FROM memories
            WHERE archived = 0
            GROUP BY tier
        ''')

        tier_counts = {row['tier']: row['count'] for row in cursor.fetchall()}
        total = sum(tier_counts.values())

        issues = []

        # Check tier distribution
        short_ratio = tier_counts.get('short', 0) / max(1, total)
        if short_ratio > 0.7:
            issues. append('Too many short-term memories')

        working_ratio = tier_counts.get('working', 0) / max(1, total)
        if working_ratio < 0.1 and total > 50:
            issues.append('Too few working memories')

        return {
            'tier_distribution': tier_counts,
            'total_memories': total,
            'issues': issues
        }

    def _check_workers_health(self) -> dict[str, Any]:
        """Check background workers health"""

        worker_pid_file = self.data_dir / 'worker_manager.pid'

        if not worker_pid_file.exists():
            return {
                'status': 'stopped',
                'running': False
            }

        try:
            with open(worker_pid_file) as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                return {
                    'status': 'running',
                    'running': True,
                    'pid': pid
                }
            else:
                return {
                    'status':  'stale',
                    'running':  False
                }

        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }

    def _get_database_size(self) -> int:
        """Get database file size in bytes"""

        db_path = Path(self.data_dir) / 'memories.db'
        if db_path.exists():
            return db_path.stat().st_size
        return 0
