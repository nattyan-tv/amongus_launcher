import requests
import flet
import os
import sys
import json
import subprocess

from typing import Callable

InstanceName = str
InstancePath = str
Instance = dict[InstanceName, InstancePath]

ModName = str
ModUrl = str
ModDescription = str

class ModClass:
    def __init__(
            self,
            name: ModName,
            description: ModDescription,
            url: ModUrl,
            depencities: list[ModName] = []
    ):
        self.name = name
        self.description = description
        self.url = url
        self.depencities = depencities

    @property
    def has_depencities(self) -> bool:
        return len(self.depencities) > 0

    def download(self, path: InstancePath):
        if not os.path.isdir(os.path.join(path, "BepInEx", "plugins")):
            os.makedirs(os.path.join(path, "BepInEx", "plugins"))
        if os.path.isfile(os.path.join(path, "BepInEx", "plugins", self.name)):
            return
        resp = requests.get(self.url)
        with open(os.path.join(path, "BepInEx", "plugins", self.name), "wb") as f:
            f.write(resp.content)

        for dep in self.depencities:
            if dep not in TemplateMods:
                continue
            TemplateMods[dep].download(path)

    def remove(self, path: InstancePath):
        os.remove(os.path.join(path, "BepInEx", "plugins", self.name))

TemplateMods: dict[ModName, ModClass] = {
    "Reactor.dll": ModClass("Reactor.dll", "様々なMODで導入が必要になる前提MOD", "https://github.com/NuclearPowered/Reactor/releases/latest/download/Reactor.dll"),
    "Submerged.dll": ModClass("Submerged.dll", "新MAP「Submerged」を追加するMOD [Reactor.dllのインストールが必要]", "https://github.com/SubmergedAmongUs/Submerged/releases/latest/download/Submerged.dll", ["Reactor.dll"]),
    "SuperNewRoles.dll": ModClass("SuperNewRoles.dll", "様々な役職を追加するMOD [Agartha.dllのインストールが必要]", "https://github.com/SuperNewRoles/SuperNewRoles/releases/latest/download/SuperNewRoles.dll", ["Agartha.dll"]),
    "Agartha.dll": ModClass("Agartha.dll", "新MAP「Agartha」を追加するMOD", "https://github.com/SuperNewRoles/SuperNewRoles/releases/latest/download/Agartha.dll"),
    "ExtremeRoles.dll": ModClass("ExtremeRoles.dll", "様々な役職を追加するMOD", "https://github.com/yukieiji/ExtremeRoles/releases/latest/download/ExtremeRoles.dll"),
    "ExtremeSkins.dll": ModClass("ExtremeSkins.dll", "ExtremeRolesで使用できるスキンを追加するMOD [ExtremeRoles.dllのインストールが必要]", "https://github.com/yukieiji/ExtremeRoles/releases/latest/download/ExtremeSkins.dll", ["ExtremeRoles.dll"]),
    "ExtremeVoiceEngine.dll": ModClass("ExtremeVoiceEngine.dll", "ExtremeRolesと合成音声連携するMOD [ExtremeRoles.dllのインストールが必要]", "https://github.com/yukieiji/ExtremeRoles/releases/latest/download/ExtremeVoiceEngine.dll", ["ExtremeRoles.dll"]),
}

def main(page: flet.Page):
    page.title = "Among Us Launcher"
    page.window_width = 1000
    page.window_height = 800

    items = []
    column_control = flet.Column(controls=items) # type: ignore

    def create_cmd(path: InstancePath) -> list[str]:
        cmd = [os.path.join(path, "Among Us.exe")]
        cmd.extend(sys.argv[1:])
        return cmd

    def start_instance(path: InstancePath):
        subprocess.Popen(create_cmd(path))
        page.window_close()

    def get_instances() -> Instance:
        if not os.path.isfile("instances.json"):
            with open("instances.json", "w") as f:
                f.write(json.dumps({"instances": {}}))
            return {}
        with open("instances.json", "r") as f:
            return json.load(f)["instances"]

    def add_instance(name: InstanceName | None = None, path: InstancePath | None = None):
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

    def remove_instance(name: InstanceName):
        instances = get_instances()
        del instances[name]
        with open("instances.json", "w") as f:
            f.write(json.dumps({"instances": instances}))
        column_control.controls = [item for item in column_control.controls if item.controls[0].controls[0].content.value != name] # type: ignore
        page.update()

    def open_instance_folder(path: InstancePath):
        subprocess.Popen(["explorer", path])

    def remove_mod(item: tuple[InstanceName, InstancePath], moditem: ModClass, update_function: Callable[[], None]):
        modalComponent = flet.AlertDialog(
            modal=True,
            title=flet.Text("削除中..."),
            content=flet.Text(f"{os.path.basename(moditem.name)}を削除しています..."),
            actions=[]
        )
        page.dialog = modalComponent
        modalComponent.open = True
        page.update()
        moditem.remove(item[1])
        modalComponent.open = False
        update_function()
        page.update()

    def add_mod(item: tuple[InstanceName, InstancePath], moditem: ModClass, update_function: Callable[[], None]):
        modalComponent = flet.AlertDialog(
            modal=True,
            title=flet.Text("ダウンロード中..."),
            content=flet.Text(f"「{moditem.name}」{'と前提MOD' if moditem.has_depencities else ''}をダウンロードしています..."),
            actions=[]
        )
        page.dialog = modalComponent
        modalComponent.open = True
        page.update()
        moditem.download(item[1])
        modalComponent.open = False
        update_function()
        page.update()

    def change_mods(item: tuple[InstanceName, InstancePath]):
        if not os.path.isdir(os.path.join(item[1], "BepInEx", "plugins")):

            def close_modal(handler):
                modalComponent.open = False
                page.update()

            modalComponent = flet.AlertDialog(
                modal=True,
                title=flet.Text("エラー"),
                content=flet.Text("MODリストを確認できませんでした。\n確認しようとしたAmong Usがバニラか、BepInExを導入していない可能性があります。"),
                actions=[
                    flet.TextButton("OK",on_click=close_modal),
                ],
                actions_alignment=flet.MainAxisAlignment.END
            )
            page.dialog = modalComponent
            modalComponent.open = True
            page.update()
            return

        modViews: flet.View | None = None
        mods: list[ModName] = []

        def update_mod_list():
            mods.clear()
            mods.extend([os.path.basename(mod) for mod in os.listdir(os.path.join(item[1], "BepInEx", "plugins")) if os.path.splitext(mod)[1] == ".dll"])

        def view_pop(handler):
            if len(page.views) > 1:
                page.views.pop()
            page.go("/back")

        def create_mod_item(moditem: ModClass) -> flet.Row:
            return flet.Row(
                [
                    flet.Column(
                        [
                            flet.Text(moditem.name, style=flet.TextThemeStyle.BODY_LARGE, color=flet.colors.PRIMARY),
                            flet.Text(moditem.description, style=flet.TextThemeStyle.BODY_SMALL)
                        ]
                    ),
                    flet.IconButton(icon=flet.icons.DELETE, on_click=(lambda _: remove_mod(item, moditem, update_mod_view)))
                    if moditem.name in mods else
                    flet.IconButton(icon=flet.icons.ADD, on_click=(lambda _: add_mod(item, moditem, update_mod_view)))
                ],
                alignment=flet.MainAxisAlignment.SPACE_BETWEEN
            )

        modViews = flet.View("/mods")

        def update_mod_view():
            update_mod_list()
            modViews.appbar = flet.AppBar(title=flet.Text(item[0]))
            modViews.controls = [flet.Column([create_mod_item(moditem) for moditem in TemplateMods.values()])]

        update_mod_view()

        page.on_view_pop = view_pop
        page.views.append(modViews)
        page.go("/mods")

    def create_item(item: tuple[InstanceName, InstancePath]):
        return flet.Row(
            [
                flet.Row([
                    flet.Column([
                        flet.TextButton(content=flet.Text(item[0], style=flet.TextThemeStyle.BODY_LARGE, color=flet.colors.PRIMARY), on_click=(lambda _: start_instance(item[1]))),
                        flet.Text(value=item[1], style=flet.TextThemeStyle.BODY_SMALL)
                    ])
                ], alignment=flet.MainAxisAlignment.START),
                flet.Row([
                    flet.IconButton(icon=flet.icons.SETTINGS, on_click=(lambda _: change_mods(item))),
                    flet.IconButton(icon=flet.icons.FOLDER, on_click=(lambda _: open_instance_folder(item[1]))),
                    flet.IconButton(icon=flet.icons.DELETE, on_click=(lambda _: remove_instance(item[0])))
                ], alignment=flet.MainAxisAlignment.END)
            ],
            alignment=flet.MainAxisAlignment.SPACE_BETWEEN
        )

    page.add(flet.Text("Among Us Launcher", style=flet.TextThemeStyle.DISPLAY_LARGE))
    page.add(flet.Text("起動したいインスタンスを選択してください", style=flet.TextThemeStyle.HEADLINE_LARGE))

    items = [create_item(item) for item in get_instances().items()]
    column_control.controls = items # type: ignore

    page.add(column_control)
    page.add(flet.Text("インスタンスの追加", style=flet.TextThemeStyle.HEADLINE_LARGE))

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
