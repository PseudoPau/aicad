# AI CAD 项目环境一键配置脚本
# 适用环境: Windows PowerShell

Write-Host "--- 开始配置 AI CAD 开发环境 ---" -ForegroundColor Cyan

# 1. 配置 Conda 国内镜像源 (清华源)
Write-Host "[1/4] 配置清华镜像源..." -ForegroundColor Yellow
conda config --set show_channel_urls yes
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
Write-Host "镜像源配置完成。" -ForegroundColor Green

# 2. 创建 Conda 环境
Write-Host "[2/4] 创建名为 'cad' 的隔离环境 (Python 3.10)..." -ForegroundColor Yellow
conda create -n cad python=3.10 -y
Write-Host "环境创建成功。" -ForegroundColor Green

# 3. 安装 CadQuery
Write-Host "[3/4] 安装 CadQuery 几何引擎 (从镜像源获取)..." -ForegroundColor Yellow
conda install -n cad cadquery -y
Write-Host "CadQuery 安装完成。" -ForegroundColor Green

# 4. 安装 ocp-vscode 预览插件库
Write-Host "[4/4] 通过 pip 安装 ocp-vscode 预览组件..." -ForegroundColor Yellow
# 获取 cad 环境下的 python 路径进行精准安装
$pythonPath = "$(conda info --base)\envs\cad\python.exe"
& $pythonPath -m pip install ocp-vscode
Write-Host "ocp-vscode 安装完成。" -ForegroundColor Green

Write-Host "--- 所有配置已完成！ ---" -ForegroundColor Cyan
Write-Host "请在 VS Code 中选择 'cad' 环境作为 Python 解释器。" -ForegroundColor White