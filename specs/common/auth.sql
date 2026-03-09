-- AUTH SERVICE - db_auth
-- Таблицы: users, refresh_tokens, staff_profiles


CREATE SCHEMA IF NOT EXISTS "auth";


CREATE TABLE "auth"."users" (
    "id" BIGSERIAL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "phone" VARCHAR(20) UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100),
    "avatar_url" TEXT,
    "is_active" BOOLEAN DEFAULT TRUE,
    "is_verified" BOOLEAN DEFAULT FALSE,
    "privacy_policy_accepted_at" TIMESTAMP WITH TIME ZONE,
    "default_address" TEXT,
    "preferences_json" JSONB DEFAULT '{}',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMP WITH TIME ZONE
);


CREATE TABLE "auth"."refresh_tokens" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "token_hash" VARCHAR(255) NOT NULL UNIQUE,
    "ip_address" INET,
    "user_agent" TEXT,
    "expires_at" TIMESTAMP WITH TIME ZONE NOT NULL,
    "is_revoked" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "last_used_at" TIMESTAMP WITH TIME ZONE,
    CONSTRAINT "fk_refresh_tokens_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE
);
CREATE INDEX "refresh_tokens_idx_user" ON "auth"."refresh_tokens" ("user_id", "is_revoked");
CREATE INDEX "refresh_tokens_idx_expires" ON "auth"."refresh_tokens" ("expires_at");


CREATE TABLE "auth"."staff_profiles" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL UNIQUE,
    "venue_id" BIGINT NOT NULL, 
    "role" VARCHAR(50) DEFAULT 'staff',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "fk_staff_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE
);
CREATE INDEX "staff_profiles_idx_venue" ON "auth"."staff_profiles" ("venue_id");
CREATE INDEX "staff_profiles_idx_user" ON "auth"."staff_profiles" ("user_id");


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON "auth"."users" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
