from django.core.management.base import BaseCommand, CommandError
from screenshot_app.models import Screenshot
from screenshot_app.models import Task
import csv
import pandas
from os import listdir
import os.path
import re


class Command(BaseCommand):
    help = 'Populates database with screenshots and tasks'

    def add_arguments(self, parser):
        # parser.add_argument('folder_path_file', type=str)
        parser.add_argument('task_file', type=str)

    def handle(self, *args, **options):

        # Read Task File
        task_panda = pandas.read_csv(options['task_file'])

        # Add Screenshots to Database
        print('Adding Screenshots')
        for index, row in task_panda.iterrows():

            # Save Screenshot Object
            screenshot = Screenshot()
            screenshot.wave_id = row.wave_id
            screenshot.view_id = row.view_id
            screenshot.country = row.country
            screenshot.domain = row.domain
            screenshot.channel_id = row.channel_id
            screenshot.image_path = row.image_path
            screenshot.batch_num = 2
            screenshot.save()

        # Create Task List
        print('Generating Tasks')
        for domain in task_panda['domain'].unique():
            for country in ['USA', 'France']:
                screenshots = Screenshot.objects.filter(domain=domain, country=country, batch_num=2)
                num_screenshots = screenshots.count()
                print(str(num_screenshots) + ' screenshots found for ' + domain + ' and ' + country)
                if num_screenshots > 0:
                    task = Task()
                    task.domain = domain
                    task.country = country
                    task.save()
                    for screenshot in screenshots:
                        task.screenshots.add(screenshot)