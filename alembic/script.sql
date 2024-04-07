BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 7b3ec1d3a116

CREATE TABLE public.users (
    id SERIAL NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

INSERT INTO alembic_version (version_num) VALUES ('7b3ec1d3a116') RETURNING alembic_version.version_num;

-- Running upgrade 7b3ec1d3a116 -> 056b6a0e8866

CREATE TABLE public.book (
    id SERIAL NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES public.users (id)
);

UPDATE alembic_version SET version_num='056b6a0e8866' WHERE alembic_version.version_num = '7b3ec1d3a116';

COMMIT;
