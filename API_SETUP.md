# API 密钥配置说明

## 📝 快速开始

1. **复制示例配置文件**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**
   
   打开 `.env` 文件，填入你的 SiliconFlow API 密钥：
   ```env
   SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
   SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **获取 API 密钥**
   
   - 访问 [SiliconFlow](https://cloud.siliconflow.cn/account/ak)
   - 创建并复制你的 API 密钥
   - 粘贴到 `.env` 文件中

## ⚠️ 安全提醒

- ❌ **不要**将 `.env` 文件提交到 Git
- ✅ `.gitignore` 已配置，自动排除 `.env` 文件
- ✅ 使用 `.env.example` 作为模板分享给他人

## 🔧 其他配置

如需使用其他 API 服务，可在 `.env` 中添加：

```env
# OpenAI
OPENAI_API_KEY=your-openai-key

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
```

## 🚀 启动应用

配置完成后，直接运行：

```bash
streamlit run app_main.py
```

如果缺少 API 密钥，应用会提示错误信息。
