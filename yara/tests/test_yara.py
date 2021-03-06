#!/usr/bin/env python3

#   Copyright 2014-2018 PUNCH Cyber Analytics Group
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import yara
import unittest

from pathlib import Path

from stoq import RequestMeta, Stoq, Payload
from stoq.exceptions import StoqPluginException
from stoq.data_classes import WorkerResponse, DispatcherResponse


class TestCore(unittest.TestCase):
    def setUp(self) -> None:
        self.plugin_name = 'yara'
        self.base_dir = Path(os.path.realpath(__file__)).parent
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.plugin_dir = os.path.join(self.base_dir.parent, 'yarascan')
        self.generic_data = b'testtesttest'

    def tearDown(self) -> None:
        pass

    def test_scan(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {'worker_rules': f'{self.data_dir}/scan_rules.yar'}
            },
        )
        plugin = s.load_plugin(self.plugin_name)
        payload = Payload(self.generic_data)
        response = plugin.scan(payload, RequestMeta())
        self.assertIsInstance(response, WorkerResponse)
        self.assertEqual('test_scan_rule', response.results['matches'][0]['rule'])

    def test_scan_meta_bytes(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {'worker_rules': f'{self.data_dir}/scan_rules.yar'}
            },
        )
        plugin = s.load_plugin(self.plugin_name)
        payload = Payload(b'meta_bytes')
        response = plugin.scan(payload, RequestMeta())
        self.assertIsInstance(response, WorkerResponse)
        self.assertEqual(
            'test_scan_metadata_bytes', response.results['matches'][0]['rule']
        )
        self.assertEqual('ANeato', response.results['matches'][0]['meta']['bytes'])
        self.assertEqual(
            'Peter Rabbit', response.results['matches'][0]['meta']['author']
        )
        self.assertEqual('save_false', response.results['matches'][0]['meta']['plugin'])

    def test_scan_invalid_rule_file(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {'worker_rules': f'{self.data_dir}/nonexistent.yar'}
            },
        )
        with self.assertRaises(StoqPluginException):
            s.load_plugin(self.plugin_name)

    def test_scan_invalid_rules(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {'worker_rules': f'{self.data_dir}/invalid_rules.yar'}
            },
        )
        with self.assertRaises(yara.SyntaxError):
            s.load_plugin(self.plugin_name)

    def test_dispatcher(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {
                    'dispatch_rules': f'{self.data_dir}/dispatch_rules.yar'
                }
            },
        )
        plugin = s.load_plugin(self.plugin_name)
        payload = Payload(self.generic_data)
        response = plugin.get_dispatches(payload, RequestMeta())
        self.assertIsInstance(response, DispatcherResponse)
        self.assertIn('test_dispatch_plugin', response.plugin_names)
        self.assertEqual(
            'test_dispatch_rule', response.meta['test_dispatch_plugin']['rule']
        )
        self.assertIn(
            'test_dispatch_plugin',
            response.meta['test_dispatch_plugin']['meta']['plugin'],
        )
        self.assertIn('True', response.meta['test_dispatch_plugin']['meta']['save'])
        self.assertEqual(
            ['tag1', 'tag2'], response.meta['test_dispatch_plugin']['tags']
        )

    def test_dispatcher_save_false(self) -> None:
        s = Stoq(
            plugin_dir_list=[self.plugin_dir],
            plugin_opts={
                self.plugin_name: {
                    'dispatch_rules': f'{self.data_dir}/dispatch_rules.yar'
                }
            },
        )
        plugin = s.load_plugin(self.plugin_name)
        payload = Payload(b'save_false')
        response = plugin.get_dispatches(payload, RequestMeta())
        self.assertIsInstance(response, DispatcherResponse)
        self.assertIn('False', response.meta['save_false']['meta']['save'])
