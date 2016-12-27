import re
import os


class Writer:
    FILLED_TEMPLATES_DIR = os.path.join(os.getcwd(), 'filled_templates')

    def __init__(self, template_file):
        if not os.path.exists(template_file):
            raise FileNotFoundError('Template file is not found')
        if os.path.isabs(template_file):
            path = template_file
        else:
            path = os.path.join(os.getcwd(), template_file)
        with open(path, 'r', encoding='utf-8') as f:
            self.template = f.readlines()
        self.fields = self.extract_fields()
        self.template_name = os.path.basename(template_file)

    def extract_fields(self):
        fields = set()
        field = re.compile(r'\{\{(.*?)}}')
        for line in self.template:
            fields.update(re.findall(field, line))
        return list(fields)

    def write_filled_template(self, friends):
        if not os.path.exists(self.FILLED_TEMPLATES_DIR):
            os.makedirs(self.FILLED_TEMPLATES_DIR)
        else:
            self.clean_templates_directory()
        count = 1
        for friend in friends:
            if self.get_unrecognized_fields(friend):
                continue
            template_name, ext = os.path.splitext(self.template_name)
            template_name += str(count)
            path = os.path.join(self.FILLED_TEMPLATES_DIR, template_name + ext)
            with open(path, 'w', encoding='utf-8') as f:
                for line in self.template:
                    line = self.fill_line(friend, line)
                    f.write(line)
            count += 1

    def get_unrecognized_fields(self, friend):
        return [field for field in self.fields if (
            field not in friend._fields or getattr(friend, field) is None)]

    def fill_line(self, friend, line):
        for field in self.fields:
            pattern = '{{{{{}}}}}'.format(field)
            line = line.replace(pattern, getattr(friend, field))
        return line

    def clean_templates_directory(self, ):
        for file in os.listdir(self.FILLED_TEMPLATES_DIR):
            os.remove(os.path.join(self.FILLED_TEMPLATES_DIR, file))
