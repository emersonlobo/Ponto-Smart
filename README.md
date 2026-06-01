# Ponto Smart - Sistema de Controle de Jornada

Um sistema digital de controle de ponto desenvolvido com **Streamlit**, **Supabase** e **FPDF2**, ideal para pequenos negócios.

## 🚀 Características

- **Interface Kiosk:** Modo touch-friendly para registros rápidos de ponto.
- **Painel Administrativo:** Gestão completa de funcionários e registros.
- **Geração de Relatórios:** PDF automático com histórico de ponto.
- **Segurança:** Autenticação por PIN com bloqueio após tentativas inválidas.
- **Trilha de Auditoria:** Registro de todas as correções e alterações.
- **Modelo de assinatura:** foco em taxa mensal para o proprietário, sem cobrança por serviço dentro do aplicativo.

## 💰 Modelo de Cobrança
- Apenas uma taxa mensal paga pelo proprietário para manter o salão na plataforma.
- Sem necessidade de pagamento por atendimento ou por serviços individuais.
- Ofereça 1 mês de teste grátis para que clientes e salão possam conhecer o app e divulgar a novidade.

## 📋 Pré-requisitos

- Python 3.8+
- Conta no Supabase (https://supabase.com)
- Git (opcional)

## 🔧 Instalação

### 1. Clonar ou Baixar o Projeto

```bash
git clone <seu-repositorio>
cd ponto-smart
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Supabase

1. Acesse https://supabase.com e crie uma nova conta/projeto.
2. Copie a URL do projeto e a chave pública.
3. Abra o arquivo `.streamlit/secrets.toml` e substitua:
   - `SUPABASE_URL`: URL do seu projeto Supabase
   - `SUPABASE_KEY`: Chave pública do Supabase

### 5. Criar Tabelas no Supabase

1. Acesse o painel do Supabase.
2. Vá para "SQL Editor" e execute o script `database_schema.sql`.
3. Isso criará as tabelas `employees` e `time_entries`.

### 6. Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`.

## 📱 Como Usar

### Modo Kiosk (Funcionário)

1. Selecione seu nome na lista.
2. Digite seu PIN de 4 dígitos.
3. Clique em "Entrada" ou "Saída".
4. Veja a confirmação na tela.

**Trocar PIN:**
- Insira seu PIN atual.
- Digite o novo PIN (4 dígitos).
- Confirme o novo PIN.
- Clique em "Trocar PIN".

### Modo Administrativo

1. Clique em "Administrativo" na barra lateral.
2. Faça login com:
   - Usuário: `admin`
   - Senha: `admin123`

**Funcionalidades:**

- **Funcionários:** Adicionar, resetar PIN ou excluir funcionários.
- **Registros de Ponto:** Visualizar e corrigir registros.
- **Relatórios:** Gerar PDF com histórico de ponto.

## 🔐 Segurança

- **Imutabilidade:** Funcionários não podem editar seus próprios registros.
- **Bloqueio de PIN:** Após 3 tentativas inválidas, o sistema bloqueia por 5 minutos.
- **Trilha de Auditoria:** Todas as correções são registradas com data, hora e motivo.

## 📊 Estrutura do Banco de Dados

### Tabela: `employees`
- `id`: UUID (chave primária)
- `name`: Nome do funcionário
- `pin`: PIN de 4 dígitos
- `created_at`: Data de criação

### Tabela: `time_entries`
- `id`: UUID (chave primária)
- `employee_id`: Referência ao funcionário
- `timestamp`: Data e hora do registro
- `action`: 'entrada' ou 'saida'
- `is_corrected`: Booleano indicando se foi corrigido
- `corrected_by`: Quem realizou a correção
- `correction_reason`: Motivo da correção
- `created_at`: Data de criação

## 🚀 Deploy no Streamlit Cloud

1. Faça push do seu código para um repositório GitHub.
2. Acesse https://share.streamlit.io.
3. Selecione seu repositório e branch.
4. Configure as secrets no painel do Streamlit Cloud (adicione `SUPABASE_URL` e `SUPABASE_KEY`).
5. Clique em "Deploy".

## 🛠️ Customização

### Alterar Credenciais de Admin

Edite o arquivo `app.py`, função `admin_login()`:

```python
def admin_login(username, password):
    return username == "seu_usuario" and password == "sua_senha"
```

### Personalizar Estilos

Modifique as funções `apply_kiosk_style()` e `apply_admin_style()` no arquivo `app.py`.

## 📝 Notas Importantes

- **Modelo de negócio:** o sistema foi pensado como ferramenta de gestão e controle interno, sem gateway de pagamento integrado.
- **Portaria 671 (MTE):** Este sistema é uma ferramenta de controle gerencial interno e não substitui sistemas oficiais exigidos pela legislação brasileira.
- **Backup:** Configure backups automáticos no Supabase.
- **HTTPS:** Sempre use HTTPS em produção.

## 🐛 Troubleshooting

**Erro: "ModuleNotFoundError: No module named 'supabase'"**
- Execute: `pip install supabase`

**Erro: "SUPABASE_URL not found in secrets"**
- Verifique se o arquivo `.streamlit/secrets.toml` está configurado corretamente.

**Erro: "Connection refused"**
- Verifique sua conexão com a internet e se as credenciais do Supabase estão corretas.

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação do Supabase (https://supabase.com/docs) ou Streamlit (https://docs.streamlit.io).

## 📄 Licença

Este projeto é fornecido como está. Sinta-se livre para usar, modificar e distribuir conforme necessário.

---

**Desenvolvido com ❤️ usando Streamlit e Supabase**
