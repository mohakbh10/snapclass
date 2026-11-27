import importlib
import sys
import types
import unittest
from unittest.mock import patch


class TeacherImportContractTests(unittest.TestCase):
    def test_teacher_screen_imports_attendance_api_without_supabase_credentials(self):
        module_names = (
            'src.database.config',
            'src.database.db',
            'src.screens.teacher_screen',
        )
        missing = object()
        previous = {name: sys.modules.get(name, missing) for name in module_names}

        config_stub = types.ModuleType('src.database.config')
        config_stub.supabase = object()
        try:
            sys.modules.pop('src.database.db', None)
            sys.modules.pop('src.screens.teacher_screen', None)
            with patch.dict(sys.modules, {'src.database.config': config_stub}):
                screen = importlib.import_module('src.screens.teacher_screen')
                database = importlib.import_module('src.database.db')

                self.assertTrue(callable(database.get_attendance_for_teacher))
                self.assertIs(
                    screen.get_attendance_for_teacher,
                    database.get_attendance_for_teacher,
                )
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
                if previous[name] is not missing:
                    sys.modules[name] = previous[name]


if __name__ == '__main__':
    unittest.main()
