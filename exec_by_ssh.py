import paramiko
import sys
import os
import re
import time


class ExecBySSH:
    def __init__(self):
        self.input_file_lines = self.get_input_file()
        self.login_params = {'host': '', 'user': '', 'password': '', 'port': 22}
        self.last_line_index = 0
        self.get_login_info()
        self.client = self.login()

    def get_login_info(self):
        for index, line in enumerate(self.input_file_lines):
            line = line.strip()
            if line and re.match('^(host|user|password|port)', line):
                login_param = re.split(' *= *', line)
                if len(login_param) == 2 and login_param[0] in self.login_params.keys():
                    self.login_params[login_param[0]] = login_param[1]
            elif not self._check_login_params():
                print('login params must be at the top of input file')
                sys.exit(1)
            else:
                self.last_line_index = index
                break

    def login(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.login_params['host'], username=self.login_params['user'],
                       password=self.login_params['password'], port=self.login_params['port'])
        return client

    def exec_commands(self):
        command = ''.join(self.input_file_lines[self.last_line_index:])
        channel = self.client.get_transport().open_session()
        channel.get_pty()
        channel.exec_command(command)
        buffer = 1024
        delay = 2
        output = channel.recv(buffer).decode()
        while output:
            print(output, end='')
            if re.search('\[sudo\] password for', output):
                channel.send(self.login_params['password'] + '\n')
            output = channel.recv(4096).decode()
        print(output)
        time.sleep(delay)
        channel.close()
        self.client.close()

    def _check_login_params(self):
        return self.login_params['host'] and self.login_params['user'] and self.login_params['password'] and \
               self.login_params['port']

    @staticmethod
    def get_input_file():
        try:
            input_file_path = sys.argv[1]
            if not os.path.isfile(input_file_path):
                print('No such file {}'.format(input_file_path))
                sys.exit(1)
            input_file = open(input_file_path)
            input_file_lines = input_file.readlines()
            input_file.close()
            return input_file_lines
        except IndexError:
            print('Please enter input file')
            print('python3 <scrip name>.py <input file>')
            sys.exit(1)


ExecBySSH().exec_commands()
