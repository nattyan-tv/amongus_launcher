import flet
import os
import sys
import json
import subprocess

def main(page: flet.Page):
    page.title = "Among Us Launcher"
    page.window_width = 1000
    page.window_height = 800

    items = []
    column_control = flet.Column(controls=items) # type: ignore

    def create_cmd(path: str):
        cmd = [os.path.join(path, "Among Us.exe")]
        cmd.extend(sys.argv[1:])
        return cmd

    def start_instance(path: str):
        subprocess.Popen(create_cmd(path))
        page.window_close()

    def get_instances() -> dict[str, str]:
        if not os.path.isfile("instances.json"):
            with open("instances.json", "w") as f:
                f.write(json.dumps({"instances": {}}))
            return {}
        with open("instances.json", "r") as f:
            return json.load(f)["instances"]

    def add_instance(name: str | None = None, path: str | None = None):
        if name is None or path is None:
            return
        instances = get_instances()
        if name in instances:
            remove_instance(name)
        instances[name] = path
        with open("instances.json", "w") as f:
            f.write(json.dumps({"instances": instances}))
        column_control.controls.append(create_item((name, path)))
        page.update()

    def remove_instance(name: str):
        instances = get_instances()
        del instances[name]
        with open("instances.json", "w") as f:
            f.write(json.dumps({"instances": instances}))
        column_control.controls = [item for item in column_control.controls if item.controls[0].controls[0].content.value != name] # type: ignore
        page.update()

    def create_item(item):
        return flet.Row(
            [
                flet.Column([
                    flet.TextButton(content=flet.Text(item[0], style=flet.TextThemeStyle.BODY_LARGE, color=flet.colors.PRIMARY), on_click=(lambda _: start_instance(item[1]))),
                    flet.Text(value=item[1], style=flet.TextThemeStyle.BODY_SMALL)
                ]),
                flet.IconButton(icon=flet.icons.DELETE, on_click=(lambda _: remove_instance(item[0])))
            ],
            alignment=flet.MainAxisAlignment.SPACE_BETWEEN
        )

    page.add(flet.Text("Among Us Launcher", style=flet.TextThemeStyle.DISPLAY_LARGE))
    page.add(flet.Text("起動したいインスタンスを選択してください", style=flet.TextThemeStyle.HEADLINE_LARGE))

    items = [create_item(item) for item in get_instances().items()]
    column_control.controls = items # type: ignore

    page.add(column_control)
    page.add(flet.Text("インスタンスの追加・編集", style=flet.TextThemeStyle.HEADLINE_LARGE))

    instance_name = flet.TextField(label="インスタンス名")
    page.add(instance_name)

    pt = flet.TextField(label="パス", read_only=True)

    def choose_path(event: flet.FilePickerResultEvent):
        if event.path is None:
            return
        pt.value = event.path
        pt.update()

    fpick = flet.FilePicker(on_result=choose_path)

    page.overlay.append(fpick)

    fbtn = flet.ElevatedButton("参照", on_click=lambda _: fpick.get_directory_path(dialog_title="Among Us.exeがあるフォルダを選択してください"))

    page.add(flet.Row([
        pt,
        fbtn
    ]))
    page.add(flet.ElevatedButton("インスタンスを追加", on_click=lambda _: add_instance(instance_name.value, pt.value)))

    page.update()

if __name__ == "__main__":
    flet.app(target=main)
