import os
import imp
from django.core.management.base import BaseCommand
import api


class Command(BaseCommand):
    args = ''
    help = 'Runs parsing'

    def run_parsing(self, module_name, file_path):
        self.stdout.write('Loading %s...' % module_name)
        parsing_module = imp.load_source(module_name, file_path)
        self.stdout.write('Running %s.parse()...' % module_name)
        parsing_module.parse()

    def handle(self, *args, **options):
        parsing_path = os.path.join(os.path.dirname(api.__file__), 'parsing')
        if args:
            for module_name in args:
                file_name = module_name + '.py'
                file_path = os.path.join(parsing_path, file_name)
                self.run_parsing(module_name, file_path)
        else:
            for file_name in os.listdir(parsing_path):
                if not file_name.startswith('_') and file_name.endswith('.py'):
                    file_path = os.path.join(parsing_path, file_name)
                    module_name = file_name[:-3]
                    self.run_parsing(module_name, file_path)
