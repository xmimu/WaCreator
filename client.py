import time
from waapi.client import WaapiClient
from WType import WType


class Client(WaapiClient):
    log_file = 'log.txt'

    def __init__(self):
        super().__init__()

    @staticmethod
    def log(msg: str):
        # 获取当前时间
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        with open(Client.log_file, 'a', encoding='u8') as f:
            f.write(
                f'==================== {time_str} ===================== \n' +
                f'{msg}\n' +
                '==============================================================\n')

    @property
    def version(self) -> str:
        result = self.call('ak.wwise.core.getInfo', {})
        _version = result['version']['displayName']
        return _version

    @property
    def selected_object(self) -> list:
        options = {'return': ['id', 'name', 'type', 'path']}
        result = self.call('ak.wwise.ui.getSelectedObjects',
                           {}, options=options)
        _selected_object = result['objects']
        return _selected_object

    def on_selectionChanged(self, callback):
        options = {'return': ['id', 'name', 'type', 'path']}
        self.subscribe('ak.wwise.ui.selectionChanged',
                       callback, options)

    def create_object(self, object_type: str, object_name: str,
                      object_path: str) -> None:
        return self.call('ak.wwise.core.object.create', {
            'type': object_type,
            'name': object_name,
            'parent': object_path
        })

    def delete_object(self, object_id: str) -> None:
        return self.call('ak.wwise.core.object.delete', {
            'object': object_id
        })

    def create_work_unit(self, work_unit_name: str, parent_path: str) -> None:
        return self.create_object(WType.WORK_UNIT, work_unit_name, parent_path)


if __name__ == '__main__':
    try:
        with Client() as client:
            print(client.version)
            print(client.selected_object)
    except Exception as e:
        print(e)
