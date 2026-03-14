# freecad-cli

FreeCAD を AI Agent からシェル経由で操作するための Python CLI ツール。XML-RPC（port 9875）で FreeCAD と通信する。

## アーキテクチャ

```
AI Agent → shell → freecad-cli (Python CLI)
                        ↓ XML-RPC (localhost:9875)
                    FreeCAD + Addon (RPC Server)
```

## 使い方

```sh
freecad-cli ping
freecad-cli create-document MyDoc
freecad-cli create-object MyDoc Box MyBox --properties '{"Length": 10}'
freecad-cli get-objects MyDoc
```

すべてのコマンドは JSON で結果を返す。

```json
{"status": "ok", "data": true}
```

## 開発

### セットアップ

```sh
uv sync
```

### コマンドとして使えるようにする

```sh
uv tool install -e .
```

editable モードでインストールされるため、ソースコードの変更が即座に反映される。

アンインストールする場合:

```sh
uv tool uninstall freecad-cli
```

### テスト

```sh
uv run pytest
```
