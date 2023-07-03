import PySimpleGUI as sg
import requests as requests
import json

WATSTOKEN = 'dGVzdDoqazFRQTk5MnlZMUpZV0hwOWNLa2tZTDl4ODZ2OG8='
# request_url = 'https://akgre.wats.com/api/Report/WSJF'
# headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + WATSTOKEN}
# response = requests.post(request_url, headers=headers, data=json.dumps(json.loads(json_data)), timeout=30)

sg.theme('DefaultNoMoreNagging')

layout = [
    [sg.Text('API Token:', size=(12, 1))],
    [sg.InputText(key='api_token', size=(60, 1), default_text=WATSTOKEN)],
    [sg.Text('File:', size=(12, 1))],
    [sg.Input(key='file', size=(60, 1)), sg.FileBrowse()],
    [sg.Submit('Upload', size=(10, 1))]
]


window = sg.Window('Upload Tool', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Upload':
        print(values)
        if values['api_token'] == '':
            sg.popup('WARNING: API Key Required')
        elif values['file'] == '':
            sg.popup('No File Specified')
        else:
            api_token = values['api_token']
            file_path = values['file']
            with open(file_path) as f:
                report = f.read()
            # Do something with the API token and file here, such as uploading the file using the token
            request_url = 'https://akgre.wats.com/api/Report/WSJF'
            headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + WATSTOKEN}
            report_guid = json.loads(report)['id']
            print(report_guid)
            response = requests.post(request_url, headers=headers, data=json.dumps(json.loads(report)), timeout=30)
            # response = requests.get(f'https://akgre.wats.com/api/Report/Wsjf/{report_guid}', headers=headers,
            #                         timeout=60)
            if response.status_code != 200:
                print(response.json()['Message'])
            else:
                sg.popup(f'File uploaded successfully!\nGUID = {report_guid}')

window.close()
