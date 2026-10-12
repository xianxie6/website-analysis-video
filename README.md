# 网站拆解与实操解析视频 Skill

把网站的技术、故事、场景和业务分析，转化为有证据的报告与真实操作解析视频。

**核心原则：真实操作大画面展示，关键区域适度放大，文字精简，配音自然，结论可追溯。**

## 能做什么

- 拆解公开技术栈、叙事结构、交互场景、业务与案例。
- 将分析结论映射到真实操作录屏，记录覆盖范围和采集限制。
- 规划分镜与动画、放大操作区域、精简画面文字。
- 选择配音、对齐字幕、检查旁白与画面时长。
- 输出视频、来源说明、字幕和可编辑工程。

只要求网站分析时，停在分析报告；不会自动扩展为视频制作。

## 安装到 Codex

```bash
git clone https://github.com/xianxie6/website-analysis-video.git "${CODEX_HOME:-$HOME/.codex}/skills/website-analysis-video"
```

如果该目录已存在，请先检查本地版本，避免覆盖已有修改。重新打开会话后，可用 `$website-analysis-video` 调用。

## 使用示例

**完整解析视频：**

```text
用 $website-analysis-video 分析 https://example.com ，拆解技术、故事、场景和业务，
制作横版约 2 分钟的中文解析视频。以真实操作录屏为主，关键区域放大，
画面文字精简，配音先试听。
```

**只做研究：**

```text
用 $website-analysis-video 详细分析这个网站，输出技术证据、场景操作表和业务报告，暂不制作视频。
```

**优化现有视频：**

```text
用 $website-analysis-video 优化现有解析视频：把操作录屏放大，改成逐段展示，
删掉重复说明，保留准确字幕和现有配音。
```

## 文件结构

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | Skill 入口、流程与关键判断 |
| [references/analysis.md](references/analysis.md) | 技术证据、故事、场景与业务拆解 |
| [references/recording.md](references/recording.md) | 实操采集、录制范围与局部放大 |
| [references/editing.md](references/editing.md) | 分镜、配音、字幕与交付检查 |
| [references/funtech-case.md](references/funtech-case.md) | FUNTECH 项目的方法复盘 |
| [assets/project-manifest.example.json](assets/project-manifest.example.json) | 可复制的项目清单模板 |
| [scripts/validate_manifest.py](scripts/validate_manifest.py) | 素材、证据引用与时间窗口校验 |
| [agents/openai.yaml](agents/openai.yaml) | Codex 界面元数据 |

## 项目清单校验

脚本使用 Python 3 标准库，无需 Python 第三方依赖。`--probe` 模式需要系统可执行 `ffprobe`。

```bash
python3 scripts/validate_manifest.py /path/to/project/manifest.json
python3 scripts/validate_manifest.py /path/to/project/manifest.json --probe
```

复制模板后替换示例素材路径和时间数据；原始模板不包含媒体，不能直接作为成功校验样本。素材路径相对清单文件所在目录。

- 场景 `start` / `end`：相对整片起点，单位秒。
- 旁白 `offset` 和字幕时间：相对当前场景起点，单位秒。
- 旁白 `duration`：当前音频文件的实际长度；`rate` 是播放速度，已处理过的文件通常填 `1`。
- `capture_fps`：真实采集帧率，与最终导出 `fps` 分开记录。
- `coverage`：`complete`、`partial`、`before_after`、`not_recorded` 或 `illustration`；不完整采集需填写 `limitation`。
- `final_video` 可选；加 `--probe` 后检查实际时长、分辨率、帧率，以及要求的音轨。

校验结果以 JSON 输出；错误返回非零退出码。检查脚本不能替代观看、试听或事实核验。

## 工具与素材

这是供代理执行的工作流 Skill，浏览器操作、持续录屏、配音与视频渲染需要运行环境提供相应能力。可以配合 Remotion、ChatCut 或其他适用工具，不绑定供应商、固定音色或固定片长。

FUNTECH 复盘记录了受限采样与未完整录制的范围。推荐优先使用持续录屏，不把低帧率截图序列封装成 30 fps 当作原生 30 fps 录制。

仓库包含 Skill 文档、项目模板和校验脚本；网站素材、配音和视频成片不在本仓库中。
