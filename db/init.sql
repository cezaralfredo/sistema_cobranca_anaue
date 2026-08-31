-- =============================================================================
-- Sistema de Cobranca Anaue - PostgreSQL (dedicado e isolado)
-- Banco: sistema_cobranca | Tabela: clientes_anaue
-- notificacoes_enviadas text[] controla os estagios ja avisados,
-- evitando reenvio duplicado pelo scheduler.
-- =============================================================================

CREATE TABLE IF NOT EXISTS clientes_anaue (
    id SERIAL PRIMARY KEY,
    mongo_id VARCHAR(24) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(50),
    email VARCHAR(255),
    cobranca_status VARCHAR(50) NOT NULL DEFAULT 'pendente',
    cobranca_data_vencimento DATE,
    cobranca_pix TEXT,
    cobranca_valor NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    mensagem_customizada TEXT,
    notificacoes_enviadas TEXT[] NOT NULL DEFAULT '{}',
    criado_em TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes_anaue (cobranca_status);
CREATE INDEX IF NOT EXISTS idx_clientes_vencimento ON clientes_anaue (cobranca_data_vencimento);

-- ---------------------------------------------------------------------------
-- Seed com os clientes Anaue (aplicado na PRIMEIRA criacao, idempotente)
-- ---------------------------------------------------------------------------
INSERT INTO clientes_anaue (
    mongo_id, nome, telefone, email, cobranca_status, cobranca_data_vencimento,
    cobranca_pix, cobranca_valor, mensagem_customizada, criado_em
) VALUES
    ('69c5a4a3a0461c5be25becfb', ''Cezar Alfredo'', '5585996277707', 'gerandoparceria@gmail.com', 'pendente', '2026-08-01', NULL, 50.00, '', '2026-03-26 18:26:59.993642'),
    ('69ca6d72767f6902e924bab7', ''Unicordis'', '55 85 991572228', 'unicordisad@gmail.com', 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 50.00, '', '2026-03-30 09:32:50.129154'),
    ('69ca6d72767f6902e924bab8', ''Dinamo Engenharia'', '5585986812400', 'giuliano@dinamoeng.com', 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 150.00, '', '2026-03-30 09:32:50.279746'),
    ('69ca6d72767f6902e924bab9', ''Samaria Incorporações'', NULL, 'gyanne@samariaincorporacoes.com.br', 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 50.00, '', '2026-03-30 09:32:50.425203'),
    ('69ca6d72767f6902e924babb', ''AJS'', '5585999999924', 'antoniojose@ajsassessoria.com.br', 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 40.00, '', '2026-03-30 09:32:50.716117'),
    ('69ca6d72767f6902e924babc', ''Psicoser'', '55 85 997967648', NULL, 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 100.00, '', '2026-03-30 09:32:50.862796'),
    ('69ca6d73767f6902e924babd', ''Cidadaneando - Ernandes Oliveira'', '5585999340014', 'financeiro.eoa@gmail.com', 'pendente', '2026-09-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 40.00, '', '2026-03-30 09:32:51.008632'),
    ('69ca6d73767f6902e924babe', ''Imperial Implementos'', '5585981718410', 'imperial@imperialimplementos.com.br', 'pendente', '2026-09-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 100.00, '', '2026-03-30 09:32:51.155102'),
    ('69ca6d73767f6902e924babf', ''Roma Representação'', '5585997305408', 'comercial@romarepresentacao.com.br', 'pendente', '2026-08-05', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 65.00, '', '2026-03-30 09:32:51.300862'),
    ('69ca6d73767f6902e924bac0', ''GAS Consultoria'', '5585988743894', 'gilson@consultoriagas.com.br', 'pendente', '2026-08-01', '00020101021126330014br.gov.bcb.pix0111388010273205204000053039865802BR…', 40.00, '', '2026-03-30 09:32:51.447268'),
    ('69ca6d73767f6902e924bac1', ''Preventus'', '558587447151', 'roberto@preventusconsultoria.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:51.593066'),
    ('69ca6d73767f6902e924bac2', ''Uniplastic'', NULL, 'financeiro@uniplastic.ind.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:51.738602'),
    ('69ca6d73767f6902e924bac3', ''Center Office'', '5585997280839', 'contato@centeroffice.net.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:51.884201'),
    ('69ca6d74767f6902e924bac4', ''Eccoliberty'', NULL, 'financeiroestados@eccoliberty.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.030866'),
    ('69ca6d74767f6902e924bac5', ''Construtora RQ'', '5585996009956', 'financeiro@construtorarq.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.176374'),
    ('69ca6d74767f6902e924bac6', ''Well Morais'', '55 85 999860747', 'wellmoraisescritor@gmail.com', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.321912'),
    ('69ca6d74767f6902e924bac7', ''A Tecnogás'', '5585987660049', 'administracao@atecnogas.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.467110'),
    ('69ca6d74767f6902e924bac8', ''F2C Soluções'', '5585986428170', 'ricardobrunog@yahoo.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.612758'),
    ('69ca6d74767f6902e924bac9', ''Agil Acessibilidade - Lidi'', '5585981749951', NULL, 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.759064'),
    ('69ca6d74767f6902e924baca', ''Xavier'', '5585988615120', 'administrativo@eccontabilidade.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:52.906656'),
    ('69ca6d75767f6902e924bacd', ''JCN'', '558599908-6030', 'financeiro@consultoriajcn.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:53.345260'),
    ('69ca6d75767f6902e924bace', ''Oxitrat'', '558694143147', 'comercial@oxitrat.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:53.490568'),
    ('69ca6d75767f6902e924bacc', ''RL Baterias'', '5585999593940', NULL, 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:53.199257'),
    ('69ca6d75767f6902e924bacb', ''Edi Autos'', '5585997250047', 'autopecacidade01@gmail.com', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:53.052314'),
    ('6a6ca5e1e6ae9876c4af2ed1', ''Ergon Renováveis'', '5585981074975', NULL, 'pendente', NULL, NULL, 0.00, '', '2026-07-31T10:40:49.147726'),
    ('69ca6d75767f6902e924bad0', ''Confiance Metrologia'', '5519996996475', 'comercial@confiancemetrologia.com.br', 'pendente', NULL, NULL, 0.00, '', '2026-03-30 09:32:53.781411')
ON CONFLICT (mongo_id) DO NOTHING;
