CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    pin TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action TEXT NOT NULL, -- 'entrada' or 'saida'
    is_corrected BOOLEAN DEFAULT FALSE,
    corrected_by TEXT,
    correction_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opcional: Adicionar uma função para gerar UUIDs se não estiver disponível por padrão
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
