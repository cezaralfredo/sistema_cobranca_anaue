-- =============================================================================
-- Sistema de Cobranca Anaue - PostgreSQL (dedicado e isolado)
-- Banco: sistema_cobranca | Tabela: clientes_anaue
-- Comentado: notificacoes_enviadas texto[] controla os estagios ja avisados,
--            evitando reenvio duplicado pelo scheduler.
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
    cobranca_valor NUMERIC(10, 2) NOT NULL,
    mensagem_customizada TEXT,
    notificacoes_enviadas TEXT[] NOT NULL DEFAULT '{}',
    criado_em TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes_anaue (cobranca_status);
CREATE INDEX IF NOT EXISTS idx_clientes_vencimento ON clientes_anaue (cobranca_data_vencimento);

-- ---------------------------------------------------------------------------
-- Seed com os dados fornecidos (clientes Anaue)
-- ---------------------------------------------------------------------------
INSERT INTO clientes_anaue (
    mongo_id, nome, telefone, email, cobranca_status, cobranca_data_vencimento, cobranca_pix, cobranca_valor, mensagem_customizada, criado_em
) VALUES
('69c5a4a3a0461c5be25becfb', 'Cezar Alfredo', '5585996277707', 'gerandoparceria@gmail.com', 'pendente', '2026-08-01', '', 50.00, '', '2026-03-26 18:26:59.993642'),
('69ca6d72767f6902e924bab7', 'Unicordis', '55 85 991572228', 'unicordisad@gmail.com', 'pendente', '2026-08-01', '', 50.00, '', '2026-03-30 09:32:50.129154'),
('69ca6d72767f6902e924bab8', 'Dinamo Engenharia', '5585986812400', 'giuliano@dinamoeng.com', 'pendente', '2026-08-01', '', 150.00, '', '2026-03-30 09:32:50.279746'),
('69ca6d72767f6902e924bab9', 'Samaria Incorporacoes', NULL, 'gyanne@samariaincorporacoes.com.br', 'pendente', '2026-08-01', '', 50.00, '', '2026-03-30 09:32:50.425203'),
('69ca6d72767f6902e924babb', 'AJS', '5585999999924', 'antoniojose@ajsassessoria.com.br', 'pendente', '2026-08-01', '', 40.00, '', '2026-03-30 09:32:50.716117'),
('69ca6d72767f6902e924babc', 'Psicoser', '55 85 997967648', NULL, 'pendente', '2026-08-01', '', 100.00, '', '2026-03-30 09:32:50.862796'),
('69ca6d73767f6902e924babd', 'Cidadaneando - Ernandes Oliveira', '5585999340014', 'financeiro.eoa@gmail.com', 'pendente', '2026-09-01', '', 40.00, '', '2026-03-30 09:32:51.008632'),
('69ca6d73767f6902e924babe', 'Imperial Implementos', '5585981718410', 'imperial@imperialimplementos.com.br', 'pendente', '2026-09-01', '', 100.00, '', '2026-03-30 09:32:51.155102'),
('69ca6d73767f6902e924babf', 'Roma Representacao', '5585997305408', 'comercial@romarepresentacao.com.br', 'pendente', '2026-08-05', '', 65.00, '', '2026-03-30 09:32:51.300862'),
('69ca6d73767f6902e924bac0', 'GAS Consultoria', '5585988743894', 'gilson@consultoriagas.com.br', 'pendente', '2026-08-01', '', 40.00, '', '2026-03-30 09:32:51.447268')
ON CONFLICT (mongo_id) DO NOTHING;