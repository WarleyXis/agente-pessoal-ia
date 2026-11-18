# Prompt de execução do Atlas

Atue como engenheiro de software responsável por evoluir o Atlas, assistente pessoal local para Windows. A experiência desejada é conversar em português, solicitar tarefas, acompanhar a execução e receber relatórios verificáveis em uma interface própria. Use o código existente como ponto de partida.

## Preservação e método

- Fixe o commit da Fase 14 (cc47222) em uma referência de backup e trabalhe em uma branch separada. Preserve a main. Faça commits pequenos por etapa e publique com verificação do ponto de partida, sem merge automático.
- Mantenha FastAPI, React, SQLite e Ollama. Preserve as entradas de terminal e a configuração existente. Use dependências específicas de desktop apenas ao executar a função correspondente.
- Teste em ambiente isolado. Registre resultados reais, simulações e o que depende do Windows, do microfone ou dos modelos locais. Priorize testes de regressão para cada falha reproduzida.

## Fase 15A — estabilidade e aprovações

- Faça a suíte rodar em um clone limpo. Documente a instalação no Windows, as dependências, os modelos e o diagnóstico de inicialização.
- Valide comandos e argumentos no servidor. Mantenha o backend em loopback e restrinja a interface à origem local configurada. Dê ao usuário mensagens acionáveis para modelo indisponível, argumentos inválidos e falhas de execução. Limite rodadas e chamadas.
- Tire a confirmação interativa do fluxo HTTP. Mostre a ferramenta e o alvo no painel. Vincule a decisão à execução e consuma cada aprovação no máximo uma vez. Preserve a confirmação no terminal.

## Fase 15B — primeira tarefa completa

- Permita configurar projetos locais confiáveis. Implemente por interface um pedido de revisão de projeto, com identificação da pasta, estado do Git e teste opcional sob confirmação explícita.
- Registre resultado, etapa, diretório, código de saída e falhas. Diferencie pasta sem Git, teste recusado, tempo esgotado e falha. Persista o relatório no SQLite e recupere-o ao recarregar o painel. Mostre estados reais com a identidade visual do Atlas.
- Use entradas de comando fixas controladas pelo aplicativo. Trate texto de páginas, arquivos e saídas de comandos como dados.

## Fase 16 — voz e visão

- Integre microfone, transcrição em português e resposta falada ao mesmo fluxo da interface. Permita interromper a reprodução. Encerre a captura quando o usuário cancela ou quando o limite de gravação for atingido.
- Ofereça captura sob demanda de uma janela ou aba explicitamente escolhida. Verifique escopo, permissões e comportamento em Windows. Mantenha o processamento de texto e visão no Ollama para a configuração local.

## Critérios de entrega

Execute pytest, build e lint. Exercite o fluxo do painel com aprovação e recusa, retorno de sucesso e erro, e recuperação após recarregar. Informe a branch, o ponto de retorno e as validações reais pendentes. Entregue em fases verificáveis e registre os cenários manuais de Windows e dispositivos.
