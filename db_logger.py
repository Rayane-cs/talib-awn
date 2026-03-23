# ══════════════════════════════════════════════════════════════════════════════
#  db_logger.py  —  Talib-Awn · طالب عون
#  Database change logger - automatically updates DATABASE.md with changes
# ══════════════════════════════════════════════════════════════════════════════

import os
from datetime import datetime
from typing import Optional


class DatabaseLogger:
    """
    Logger for tracking database schema changes and updating documentation.
    """
    
    CHANGELOG_FILE = 'DATABASE.md'
    CHANGELOG_SECTION = '## 📝 Change Log'
    
    @staticmethod
    def log_change(change_type: str, description: str, author: str = 'System'):
        """
        Log a database change and update DATABASE.md
        
        Args:
            change_type: Type of change (e.g., 'Table Created', 'Column Added', 'Index Added')
            description: Detailed description of the change
            author: Who made the change (default: 'System')
        """
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        date_only = datetime.utcnow().strftime('%Y-%m-%d')
        
        change_entry = f"\n### {date_only} - {change_type}\n**Author:** {author}  \n**Time:** {timestamp}  \n**Description:** {description}\n"
        
        # Update DATABASE.md if it exists
        if os.path.exists(DatabaseLogger.CHANGELOG_FILE):
            try:
                with open(DatabaseLogger.CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find the changelog section
                if DatabaseLogger.CHANGELOG_SECTION in content:
                    # Insert new entry after the changelog header
                    parts = content.split(DatabaseLogger.CHANGELOG_SECTION)
                    if len(parts) == 2:
                        # Find the first existing entry or end of section
                        remaining = parts[1]
                        
                        # Insert after the section header
                        lines = remaining.split('\n', 2)
                        if len(lines) >= 2:
                            new_content = parts[0] + DatabaseLogger.CHANGELOG_SECTION + '\n' + lines[1] + change_entry + '\n'.join(lines[2:]) if len(lines) > 2 else parts[0] + DatabaseLogger.CHANGELOG_SECTION + '\n' + lines[1] + change_entry
                        else:
                            new_content = parts[0] + DatabaseLogger.CHANGELOG_SECTION + change_entry + remaining
                        
                        with open(DatabaseLogger.CHANGELOG_FILE, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"✅ Database change logged: {change_type}")
                        return True
                
            except Exception as e:
                print(f"⚠️  Failed to update {DatabaseLogger.CHANGELOG_FILE}: {e}")
                return False
        
        return False
    
    @staticmethod
    def log_table_creation(table_name: str, columns: list, description: str = ''):
        """Log creation of a new table."""
        cols_str = ', '.join(columns) if isinstance(columns, list) else str(columns)
        desc = f"Created table `{table_name}` with columns: {cols_str}."
        if description:
            desc += f" {description}"
        DatabaseLogger.log_change('Table Created', desc)
    
    @staticmethod
    def log_column_addition(table_name: str, column_name: str, column_type: str, description: str = ''):
        """Log addition of a new column."""
        desc = f"Added column `{column_name}` ({column_type}) to table `{table_name}`."
        if description:
            desc += f" {description}"
        DatabaseLogger.log_change('Column Added', desc)
    
    @staticmethod
    def log_column_modification(table_name: str, column_name: str, old_type: str, new_type: str, description: str = ''):
        """Log modification of a column."""
        desc = f"Modified column `{column_name}` in table `{table_name}`: {old_type} → {new_type}."
        if description:
            desc += f" {description}"
        DatabaseLogger.log_change('Column Modified', desc)
    
    @staticmethod
    def log_index_creation(table_name: str, index_name: str, columns: list):
        """Log creation of an index."""
        cols_str = ', '.join(columns) if isinstance(columns, list) else str(columns)
        desc = f"Created index `{index_name}` on table `{table_name}` for columns: {cols_str}."
        DatabaseLogger.log_change('Index Created', desc)
    
    @staticmethod
    def log_constraint_addition(table_name: str, constraint_type: str, description: str):
        """Log addition of a constraint."""
        desc = f"Added {constraint_type} constraint to table `{table_name}`: {description}"
        DatabaseLogger.log_change('Constraint Added', desc)
    
    @staticmethod
    def log_migration(migration_name: str, description: str):
        """Log a complete migration."""
        desc = f"Migration `{migration_name}`: {description}"
        DatabaseLogger.log_change('Migration Applied', desc)
    
    @staticmethod
    def log_custom_change(title: str, description: str, author: str = 'System'):
        """Log a custom database change."""
        DatabaseLogger.log_change(title, description, author)


# Convenience functions
def log_db_change(change_type: str, description: str, author: str = 'System'):
    """Convenience wrapper for logging database changes."""
    return DatabaseLogger.log_change(change_type, description, author)


def log_table(table_name: str, columns: list, description: str = ''):
    """Convenience wrapper for logging table creation."""
    return DatabaseLogger.log_table_creation(table_name, columns, description)


def log_column(table_name: str, column_name: str, column_type: str, description: str = ''):
    """Convenience wrapper for logging column addition."""
    return DatabaseLogger.log_column_addition(table_name, column_name, column_type, description)


# Example usage:
if __name__ == '__main__':
    # Test logging
    DatabaseLogger.log_table_creation(
        'test_table',
        ['id', 'name', 'email', 'created_at'],
        'Test table for demonstration'
    )
    
    DatabaseLogger.log_column_addition(
        'users',
        'last_login',
        'DateTime',
        'Track user last login timestamp'
    )
    
    DatabaseLogger.log_migration(
        '001_add_user_preferences',
        'Added user preferences table for storing user settings and configurations'
    )
    
    print("\n✅ Database logger test completed. Check DATABASE.md for updates.")
