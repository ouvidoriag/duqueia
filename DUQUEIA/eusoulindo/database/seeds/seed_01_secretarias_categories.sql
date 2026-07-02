-- seed_01_secretarias_categories.sql
-- Duque IA — Dados iniciais de Secretarias e Categorias
-- Gerado em: 2026-06-30 12:07:58

BEGIN TRANSACTION;

-- Secretarias
DELETE FROM secretarias;
INSERT INTO secretarias VALUES ('1', 'Secretaria Municipal de Fazenda', 'SMF');
INSERT INTO secretarias VALUES ('2', 'Secretaria Municipal de Governo', 'SG');
INSERT INTO secretarias VALUES ('3', 'Secretaria Municipal de Meio Ambiente', 'SMMA');
INSERT INTO secretarias VALUES ('4', 'Secretaria Municipal de Transportes e Serviços Públicos', 'SMT');
INSERT INTO secretarias VALUES ('5', 'Secretaria Municipal de Urbanismo e Habitação', 'SMU');
INSERT INTO secretarias VALUES ('6', 'Secretaria Municipal de Defesa Civil', 'SDC');
INSERT INTO secretarias VALUES ('7', 'Secretaria Municipal de Gestão, Inclusão e Mulher', 'SGIM');
INSERT INTO secretarias VALUES ('8', 'Secretaria Municipal de Obras e Agricultura', 'SMO');
INSERT INTO secretarias VALUES ('9', 'Secretaria Municipal de Proteção Animal', 'SPA');
INSERT INTO secretarias VALUES ('10', 'Secretaria Municipal de Assistência Social e Direitos Humanos', 'SMASDH');
INSERT INTO secretarias VALUES ('11', 'Secretaria Municipal de Desenvolvimento Econômico', 'SDE');
INSERT INTO secretarias VALUES ('12', 'Secretaria Municipal de Educação', 'SME');
INSERT INTO secretarias VALUES ('13', 'Secretaria Municipal de Cultura e Turismo', 'SMC');
INSERT INTO secretarias VALUES ('14', 'Secretaria Municipal de Saúde', 'SMS');
INSERT INTO secretarias VALUES ('15', 'Secretaria Municipal de Ação Comunitária – SEMAC - Caxias', 'SAC–S');
INSERT INTO secretarias VALUES ('16', 'Secretaria Municipal de Esporte e Lazer', 'SEL');

-- Categorias
DELETE FROM categories;
INSERT INTO categories VALUES ('1', '1', 'Fiscalização e Tributos');
INSERT INTO categories VALUES ('2', '2', 'Governo');
INSERT INTO categories VALUES ('3', '3', 'Meio Ambiente');
INSERT INTO categories VALUES ('4', '4', 'Transportes e Serviços Públicos');
INSERT INTO categories VALUES ('5', '5', 'Urbanismo e Habitação');
INSERT INTO categories VALUES ('6', '6', 'Defesa Civil');
INSERT INTO categories VALUES ('7', '7', 'Gestão, Inclusão e Mulher');
INSERT INTO categories VALUES ('8', '8', 'Obras e Agricultura');
INSERT INTO categories VALUES ('9', '9', 'Proteção Animal');
INSERT INTO categories VALUES ('10', '10', 'Assistência Social e Direitos Humanos');
INSERT INTO categories VALUES ('11', '11', 'Desenvolvimento Econômico');
INSERT INTO categories VALUES ('12', '12', 'Educação');
INSERT INTO categories VALUES ('13', '13', 'Cultura e Turismo');
INSERT INTO categories VALUES ('14', '13', 'Fundec');
INSERT INTO categories VALUES ('15', '14', 'Saúde');
INSERT INTO categories VALUES ('16', '15', 'Ação Comunitária (SEMAC)');
INSERT INTO categories VALUES ('17', '16', 'Esporte e Lazer');

COMMIT;