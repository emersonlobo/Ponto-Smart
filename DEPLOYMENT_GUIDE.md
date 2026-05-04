# Guia de Implantação - Ponto Smart

Este documento fornece um passo a passo completo para implantar o sistema Ponto Smart em um ambiente de produção.

## 📋 Checklist de Pré-Implantação

- [ ] Conta Supabase criada
- [ ] Projeto Supabase configurado
- [ ] Tabelas do banco de dados criadas
- [ ] Credenciais do Supabase obtidas
- [ ] Tablet/Dispositivo preparado
- [ ] Conexão de internet testada
- [ ] Funcionários cadastrados no sistema

## 🔧 Passo 1: Configurar o Supabase

### 1.1 Criar Projeto no Supabase

1. Acesse https://supabase.com
2. Clique em "New Project"
3. Preencha os dados:
   - **Name:** Ponto Smart
   - **Database Password:** Crie uma senha forte
   - **Region:** Selecione a região mais próxima (ex: São Paulo)
4. Clique em "Create new project"

### 1.2 Obter Credenciais

1. Após criar o projeto, vá para "Settings" > "API"
2. Copie:
   - **Project URL** (será seu `SUPABASE_URL`)
   - **anon public** (será seu `SUPABASE_KEY`)

### 1.3 Criar Tabelas

1. Vá para "SQL Editor"
2. Clique em "New Query"
3. Cole o conteúdo do arquivo `database_schema.sql`
4. Clique em "Run"

## 🖥️ Passo 2: Instalar a Aplicação Localmente

### 2.1 Preparar o Ambiente

```bash
# Clone ou baixe o projeto
cd ponto-smart

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### 2.2 Configurar Credenciais

1. Abra `.streamlit/secrets.toml`
2. Substitua com suas credenciais do Supabase:
   ```toml
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_KEY = "sua-chave-publica"
   ```

### 2.3 Testar Localmente

```bash
streamlit run app.py
```

Acesse http://localhost:8501 e teste:
- Modo Kiosk (adicione um funcionário de teste)
- Modo Admin (login: admin / senha: admin123)

## ☁️ Passo 3: Deploy no Streamlit Cloud

### 3.1 Preparar Repositório GitHub

```bash
# Inicialize um repositório Git (se não tiver)
git init
git add .
git commit -m "Initial commit: Ponto Smart"
git branch -M main
git remote add origin https://github.com/seu-usuario/ponto-smart.git
git push -u origin main
```

### 3.2 Deploy no Streamlit Cloud

1. Acesse https://share.streamlit.io
2. Clique em "New app"
3. Selecione seu repositório e branch
4. Preencha:
   - **Repository:** seu-usuario/ponto-smart
   - **Branch:** main
   - **Main file path:** app.py
5. Clique em "Deploy"

### 3.3 Configurar Secrets

1. No painel do Streamlit Cloud, vá para "Settings"
2. Clique em "Secrets"
3. Adicione:
   ```toml
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_KEY = "sua-chave-publica"
   ```
4. Clique em "Save"

## 📱 Passo 4: Configurar o Tablet (Modo Kiosk)

### 4.1 Preparar o Tablet

1. Conecte o tablet à rede Wi-Fi
2. Abra um navegador (Chrome, Firefox, Safari)
3. Acesse a URL do seu aplicativo Streamlit Cloud

### 4.2 Ativar Modo Kiosk (Opcional)

**Android:**
- Use um aplicativo como "Kiosk Browser" ou "Fully Kiosk Browser"
- Configure para abrir automaticamente a URL do Ponto Smart

**iOS:**
- Use "Guided Access" para bloquear o tablet no aplicativo

### 4.3 Configurar Autostart

- Configure o tablet para ligar automaticamente em horários específicos
- Configure o navegador para abrir automaticamente a URL

## 👥 Passo 5: Cadastrar Funcionários

### 5.1 Acessar Painel Admin

1. Abra a aplicação
2. Selecione "Administrativo" na barra lateral
3. Faça login com admin / admin123

### 5.2 Adicionar Funcionários

1. Vá para "Funcionários"
2. Clique em "Adicionar Novo Funcionário"
3. Preencha:
   - **Nome do Funcionário:** Nome completo
   - **PIN:** 4 dígitos (ex: 1234)
4. Clique em "Adicionar"

## 🎓 Passo 6: Treinar Funcionários

### 6.1 Demonstração

1. Reúna os funcionários
2. Mostre como usar o Kiosk:
   - Selecionar nome
   - Digitar PIN
   - Clicar em Entrada/Saída
   - Visualizar confirmação

### 6.2 Prática

1. Deixe cada funcionário praticar 2-3 vezes
2. Responda dúvidas
3. Confirme que todos entenderam

## 📊 Passo 7: Monitoramento

### 7.1 Verificar Registros

1. Acesse o Painel Admin
2. Vá para "Registros de Ponto"
3. Verifique se os registros estão sendo salvos corretamente

### 7.2 Gerar Relatórios

1. Vá para "Relatórios"
2. Selecione um funcionário e período
3. Clique em "Gerar Relatório PDF"
4. Baixe e verifique o PDF

## 🔒 Passo 8: Segurança

### 8.1 Alterar Credenciais de Admin

1. Abra `app.py`
2. Localize a função `admin_login()`
3. Altere o usuário e senha:
   ```python
   def admin_login(username, password):
       return username == "novo_usuario" and password == "nova_senha"
   ```
4. Faça deploy novamente

### 8.2 Backup do Banco de Dados

1. Acesse o Supabase
2. Vá para "Database" > "Backups"
3. Configure backups automáticos

## 🚀 Passo 9: Otimizações

### 9.1 Melhorar Performance

- Configure cache no navegador
- Use uma conexão de internet de alta velocidade
- Considere usar um tablet com processador mais potente

### 9.2 Customização

- Altere cores e logos no arquivo `app.py`
- Adicione seu logo da empresa
- Customize mensagens de boas-vindas

## 📞 Troubleshooting

| Problema | Solução |
|----------|---------|
| Tablet não conecta | Verifique Wi-Fi, reinicie o tablet |
| Erro de autenticação | Verifique credenciais do Supabase |
| Registros não salvam | Verifique conexão com internet e banco de dados |
| Relatório não gera | Verifique se há registros no período selecionado |

## ✅ Checklist de Pós-Implantação

- [ ] Todos os funcionários conseguem registrar ponto
- [ ] Relatórios estão sendo gerados corretamente
- [ ] Backups estão configurados
- [ ] Credenciais de admin foram alteradas
- [ ] Tablet está configurado em modo kiosk
- [ ] Equipe foi treinada
- [ ] Documentação foi distribuída

## 📝 Próximos Passos

1. **Semana 1:** Monitoramento diário
2. **Semana 2:** Ajustes finos baseado em feedback
3. **Semana 3-4:** Consolidação e eliminação do sistema antigo
4. **Mês 2+:** Análise de dados e otimizações

---

**Parabéns! Seu sistema Ponto Smart está pronto para uso! 🎉**
