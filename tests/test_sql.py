# -*- coding: utf-8 -*-

from unittest import TestCase, main
from mock import MagicMock, call

from mongo_connector.doc_managers import sql, utils
from bson.objectid import ObjectId

from collections import OrderedDict
from datetime import datetime
from .fixtures import *


class TestPostgreSQL(TestCase):
    def test_to_sql_list(self):
        items = ['1', '2']
        got = sql.to_sql_list(items)
        self.assertEqual(got, ' (1,2) ')

    def test_sql_table_exists(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = [1]
        got = sql.sql_table_exists(cursor, 'table')

        self.assertEqual(len(cursor.execute.call_args[0]), 1)
        self.assertIn('table', cursor.execute.call_args[0][0])
        self.assertEqual(got, 1)

    def test_sql_delete_rows(self):
        cursor = MagicMock()
        sql.sql_delete_rows(cursor, 'table')
        cursor.execute.assert_called_with('DELETE FROM table')

    def test_sql_delete_rows_where(self):
        cursor = MagicMock()
        sql.sql_delete_rows_where(cursor, 'table', 'id = 1')
        cursor.execute.assert_called_with('DELETE FROM table WHERE id = 1')

    def test_sql_drop_table(self):
        cursor = MagicMock()
        sql.sql_drop_table(cursor, 'table')
        cursor.execute.assert_called_with('DROP TABLE IF EXISTS table CASCADE')

    def test_sql_create_table(self):
        cursor = MagicMock()
        columns = [
            'id INTEGER',
            'field TEXT'
        ]
        sql.sql_create_table(cursor, 'table', columns)
        cursor.execute.assert_called_with(
            'CREATE TABLE table  (field TEXT,id INTEGER) '
        )

    def test_sql_add_foreign_keys(self):
        cursor = MagicMock()
        foreign_keys = [
            {
                'table': 'table',
                'fk': 'reftable_id',
                'ref': 'reftable',
                'pk': 'id'
            }
        ]

        sql.sql_add_foreign_keys(cursor, foreign_keys)
        cursor.execute.assert_called_with(
            'ALTER TABLE table ADD CONSTRAINT table_reftable_id_fk FOREIGN KEY (reftable_id) REFERENCES reftable(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED'
        )

    def test_sql_bulk_insert(self):
        cursor = MagicMock()

        mapping = {
            'db': {
                'col': {
                    'pk': '_id',
                    'field1': {
                        'type': 'TEXT',
                        'dest': 'field1'
                    },
                    'field2.subfield': {
                        'type': 'TEXT',
                        'dest': 'field2_subfield'
                    }
                }
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [])

        cursor.execute.assert_not_called()

        doc = {
            '_id': 'foo',
            'field1': 'val'
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [doc])
        cursor.execute.assert_called_with(TEST_SQL_BULK_INSERT_1)

        doc = {
            '_id': 'foo',
            'field1': 'val1',
            'field2': {
                'subfield': 'val2'
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [doc])
        cursor.execute.assert_called_with(TEST_SQL_BULK_INSERT_2)

    def test_sql_bulk_insert_array(self):
        cursor = MagicMock()

        mapping = {
            'db': {
                'col1': {
                    'pk': '_id',
                    '_id': {
                        'type': 'INT'
                    },
                    'field1': {
                        'dest': 'col_array',
                        'type': '_ARRAY',
                        'fk': 'id_col1'
                    },
                    'field2': {
                        'dest': 'col_scalar',
                        'fk': 'id_col1',
                        'valueField': 'scalar',
                        'type': '_ARRAY_OF_SCALARS'
                    }
                },
                'col_array': {
                    'pk': '_id',
                    '_id': {
                        'dest': '_id',
                        'type': 'SERIAL'
                    },
                    'field1': {
                        'dest': 'field1',
                        'type': 'TEXT'
                    },
                    'id_col1': {
                        'dest': 'id_col1',
                        'type': 'INT'
                    }
                },
                'col_scalar': {
                    'pk': '_id',
                    '_id': {
                        'dest': '_id',
                        'type': 'SERIAL'
                    },
                    'scalar': {
                        'dest': 'scalar',
                        'type': 'INT'
                    },
                    'id_col1': {
                        'dest': 'id_col1',
                        'type': 'INT'
                    }
                }
            }
        }

        doc = {
            '_id': 1,
            'field1': [
                {'field1': 'val'}
            ],
            'field2': [1, 2, 3]
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col1', [doc, {'_id': 2}])


        cursor.execute.assert_has_calls([
            call(TEST_SQL_BULK_INSERT_ARRAY_1),
            call(TEST_SQL_BULK_INSERT_ARRAY_2)
        ])


if __name__ == '__main__':
    main()
