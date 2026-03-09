import uuid
from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class Lesson(Base):
    __tablename__ = "lessons"

    # --- CHAVES E RELACIONAMENTOS ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    turma_id = Column(UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("professores.id"), nullable=True)
    disciplina_id = Column(UUID(as_uuid=True), ForeignKey("disciplinas.id"), nullable=True)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    criado_por = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # --- DADOS BASE ---
    disciplina = Column(String, nullable=False) 
    data_aula = Column(Date, nullable=False)
    conteudo = Column(String, nullable=False)
    bloco = Column(Integer, nullable=True)
    
    # --- NOVO: Transmissão ---
    # Copiado da Grade, mas editável pelo Assistente no dia da aula
    canal_iptv = Column(Integer, nullable=True) 
    
    # --- CONTROLE DE CONFORMIDADE ---
    status_transmissao = Column(String, default="agendada", nullable=False) 
    status_compliance = Column(String, default="amarelo", nullable=False)
    is_draft = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    
    # --- DADOS OPERACIONAIS E AUDITORIA ---
    professor_substituido = Column(Boolean, default=False)
    motivo_substituicao = Column(Text, nullable=True)
    interacao_turma = Column(Boolean, default=False)
    atividade_pratica = Column(Text, nullable=True)
    atraso_minutos = Column(Integer, default=0)
    obs_atraso = Column(Text, nullable=True)
    problema_material = Column(String, nullable=True)
    recursos_utilizados = Column(JSONB, nullable=True)
    observacoes_gerais = Column(Text, nullable=True)
    
    justificativa_cancelamento = Column(Text, nullable=True)
    nome_padronizado = Column(String, nullable=False, unique=True)
    
    # --- LINKS EXTERNOS ---
    video_link = Column(String, nullable=True)
    pdf_link = Column(String, nullable=True)