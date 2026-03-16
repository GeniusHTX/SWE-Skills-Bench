<p align="center">
  <strong>SWE-Skills-Bench</strong>
</p>

<p align="center">一个用于验证 Agent Skill 在真实软件工程任务中是否带来稳定收益的可复现实验框架</p>

<p align="center">
  <strong><a href="README.md">English</a></strong>
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB">
  </a>
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Required-2496ED">
  <img alt="CLI" src="https://img.shields.io/badge/CLI-Click-5C4EE5">
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
  </a>
</p>

## 项目简介

这个仓库用于做 skill 对照实验：尽量固定任务、仓库、测试和容器环境，只改变是否注入 skill、是否启用 agent，观察结果是否改善。

工作流分为两个阶段：

1. `main.py run`：创建容器、准备仓库、执行 Claude 交互。
2. `eval.py`：附着到已有容器并执行评估。

`eval.py` 输出的是原始实验结果，不是论文最终指标。论文里的通过率、失败分析、token 成本等结果，需要在 `eval` 之后继续用 `scripts/` 下的脚本统计。

## 目录速览

```text
config/benchmark_config.yaml   全局配置与 skill 定义
skills/<skill-id>/SKILL.md     skill 内容
tasks/<skill-id>.md            任务描述
tests/test_<skill-id>.py       评估测试
main.py                        运行入口
eval.py                        评估入口
run_all_skills.py              批量运行
run_all_skills_eval.py         批量评估
scripts/                       指标后处理脚本
reports/                       运行与评估报告
claude_process/                Claude 输出与 thinking 日志
```

## 运行前准备

- Python 3.8+
- Docker 已启动
- 容器镜像内可直接使用 `claude` 命令
- 已配置 Claude/Anthropic 认证信息

注意：本仓库使用的 Docker 镜像托管在 Docker Hub 的 `zhangyiiiiii` 命名空间（例如：`zhangyiiiiii/swe-skills-bench-python[:tag]`）。`config/benchmark_config.yaml` 中引用了这些镜像；如果省略 tag，Docker 会尝试拉取 `:latest`（前提是该标签存在）。为保证实验可重复性，建议使用明确的 tag。 

安装依赖：

```bash
pip install -r requirements.txt
```

配置环境变量：

```bash
cp .env.example .env
```

Windows 也可以直接复制 `.env.example` 为 `.env`。至少需要填写：

```text
ANTHROPIC_AUTH_TOKEN=your-anthropic-api-key
ANTHROPIC_BASE_URL=
```

## Claude 模型配置

可以通过工作区下的 `.claude/settings.json` 配置容器内 Claude Code 的模型与相关参数。运行 `main.py run` 时，框架会读取这个文件，并将其复制到容器内的 `/home/dev/.claude/settings.json`。

因此，调整 Claude Code 所用模型的推荐方式是：先修改 `.claude/settings.json`，再重新执行实验。

## 快速开始

```bash
python main.py validate --config config/benchmark_config.yaml
python main.py list-skills --config config/benchmark_config.yaml
python main.py run -s add-uint-support -c config/benchmark_config.yaml
python eval.py -s add-uint-support --use-skill --use-agent
```

默认情况下，运行报告写入 `reports/interactive`，评估报告写入 `reports/eval`。

## 常用实验组合

| 组合 | 含义 |
| --- | --- |
| `--use-skill --use-agent` | 注入 skill，并执行 agent |
| `--no-use-skill --use-agent` | 不注入 skill，只比较 agent 本身 |
| `--use-skill --no-use-agent` | 注入 skill，但跳过 agent 交互 |
| `--no-use-skill --no-use-agent` | 纯对照条件 |

做对照实验时，`run` 和 `eval` 阶段需要使用同一组标志位。

## 后处理与论文指标

推荐流程：

1. 运行 `main.py run`
2. 运行 `eval.py`
3. 运行后处理脚本

常用脚本：

- `python scripts/compare_pass_rate.py -s <skill_id>`：比较 L2 测试通过率
- `python scripts/extract_failed_tests.py`：提取失败测试并做对比
- `python scripts/analyze_tokens.py`：统计 token 和执行时长

常见输出目录：

- `reports/compare`
- `reports/failed_test`
- `reports/token_and_duration`

## 批量运行

```bash
python run_all_skills.py
python run_all_skills_eval.py
```

常见附加参数包括 `--dry-run`、`--resume`、`--only`、`--skip`、`--no-use-skill`、`--no-use-agent`。

## 新增一个 Skill

最小可运行单元通常包含：

1. `skills/<skill-id>/SKILL.md`
2. `tasks/<skill-id>.md`
3. `tests/test_<skill-id>.py`
4. `config/benchmark_config.yaml` 中的对应配置

新增后建议先执行：

```bash
python main.py validate --config config/benchmark_config.yaml
python main.py run -s <skill-id>
python eval.py -s <skill-id> --use-skill --use-agent
```

## 常见问题

### `claude` 不存在

请确认目标镜像中已经安装 Claude Code CLI，并且 `claude` 在容器 PATH 中。

### `eval.py` 找不到容器

通常是因为 `skill_id`、`use-skill`、`use-agent` 与运行阶段不一致，或者运行后已清理容器。

### Docker 占用越来越大

项目默认保留容器，方便后续评估和排查。可用下面的脚本清理：

```bash
python scripts/clean_container.py --all
```

## 许可证

MIT. See `LICENSE` for details.
