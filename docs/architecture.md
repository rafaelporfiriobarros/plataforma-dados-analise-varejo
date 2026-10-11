# Arquitetura e decisões técnicas

## Objetivo

Criar um pipeline reprodutível para transformar duas fontes de vendas em dados confiáveis e consumíveis por Analytics, mantendo rastreabilidade entre origem, transformação e entrega.

## Camadas

### Raw / Bronze
Preserva a entrada e permite rastrear o dado recebido. A regra é minimizar transformações nesta etapa.

### Silver
Concentra padronização de tipos, datas, valores monetários e semântica de campos. Também é o ponto em que os principais checks de qualidade são aplicados.

### Gold
Representa a camada de consumo. Contém modelo dimensional, marts e views com métricas prontas para BI.

## Orquestração

O Airflow agenda `mercado_analytics_daily`, mantém histórico e aplica retries. O DAG chama o pipeline como uma unidade reproduzível, em vez de duplicar regras dentro da definição da DAG.

## Observabilidade

`audit.pipeline_runs` registra execuções do pipeline. `audit.data_quality_results` registra os checks executados. Isso separa dados de negócio de metadados operacionais.

## Idempotência

A carga incremental utiliza chaves de negócio para impedir duplicação na Silver. O CI executa o pipeline duas vezes contra PostgreSQL para verificar esse comportamento.

## Por que PostgreSQL?

O volume atual não exige tecnologia distribuída. PostgreSQL é suficiente para demonstrar persistência, SQL, schemas, constraints, modelagem dimensional e integração com BI sem introduzir complexidade artificial.

## Por que não Spark/Kafka/Kubernetes?

As fontes são arquivos pequenos e batch. Essas tecnologias não resolveriam uma limitação concreta do dataset atual e aumentariam o custo operacional do projeto. Uma mudança de arquitetura deve ser motivada por volume, velocidade, disponibilidade ou requisitos de integração reais.
