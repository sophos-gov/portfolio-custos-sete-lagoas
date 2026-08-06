# Instruções para Publicar no GitHub Pages

## 1. Criar Repositório no GitHub

Acesse https://github.com/new e crie um repositório chamado:
- Nome: `portfolio-custos-sete-lagoas` (ou outro nome de sua preferência)
- Visibilidade: **Public** (necessário para GitHub Pages)
- Não inicializar com README (já temos um)

## 2. Adicionar Remote e Fazer Push

Após criar o repositório, copie a URL SSH (ex: `git@github.com:sophos-gov/portfolio-custos-sete-lagoas.git`) e execute:

```bash
cd "C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\"

# Adicionar remote (substitua pela URL do seu repositório)
git remote add origin git@github.com:sophos-gov/portfolio-custos-sete-lagoas.git

# Fazer push da branch master
git push -u origin master

# Fazer push da branch gh-pages (importante para publicação)
git push -u origin gh-pages
```

## 3. Configurar GitHub Pages

No repositório GitHub:
1. Vá em **Settings** → **Pages**
2. Em "Source", selecione:
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. Clique em "Save"

## 4. Acessar o Site

Seu site estará disponível em:
```
https://seu-usuario.github.io/portfolio-custos-sete-lagoas/
```

Exemplo (se a organização for `sophos-gov`):
```
https://sophos-gov.github.io/portfolio-custos-sete-lagoas/
```

## 5. Atualizar o Site (Futuro)

Para atualizar o portfólio no futuro:

```bash
# Edite os arquivos conforme necessário
# Por exemplo: cardapio_unificado.html

# Regenere as variantes
python gerar_artifact.py
python gerar_editavel.py

# Faça commit
git add cardapio_unificado.html cardapio_unificado_artifact.html cardapio_unificado_editavel_artifact.html
git commit -m "Atualizar portfólio: [descrição das mudanças]"

# Faça push nas duas branches
git push origin master
git push origin gh-pages
```

## Status Atual

- ✅ Repositório local criado
- ✅ Branch `master` com todos os arquivos e README
- ✅ Branch `gh-pages` com arquivos HTML para publicação
- ⏳ Aguardando: Criação do repositório remoto no GitHub

---

**Nota**: Se estiver usando HTTPS em vez de SSH, use:
```bash
git remote add origin https://github.com/sophos-gov/portfolio-custos-sete-lagoas.git
```
