import time
import os
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import get_settings
from app.models.class_report import ClassReport
from app.services.sync_drive import buscar_video_no_drive

settings = get_settings()

@celery_app.task(
    bind=True, 
    name="verificar_compliance_drive", 
    max_retries=15, 
    autoretry_for=(Exception,), 
    retry_backoff=True, 
    retry_backoff_max=86400, 
    retry_jitter=True
)
def verificar_compliance_drive(self, report_id: str, nome_padronizado: str):
    """
    Busca o arquivo no Drive e garante a gravação do link no banco de dados.
    Conforme especificação §6.
    """
    print(f"[WORKER] 🔍 Verificando compliance para relatório: {nome_padronizado} (ID: {report_id})")
    
    db = SessionLocal()
    try:
        # 1. Busca no Drive
        video_drive = buscar_video_no_drive(nome_padronizado)
        
        # 2. Busca o relatório no banco
        report = db.query(ClassReport).filter(ClassReport.id == report_id).first()

        if not report:
            print(f"[WORKER] ❌ Erro: Relatório {report_id} não encontrado.")
            return False

        if not video_drive:
            print(f"[WORKER] ⚠️ Vídeo NÃO encontrado no Drive para: {nome_padronizado}")
            report.status_compliance = "Pendente"
            report.video_link = None
            db.commit()

            # Dispara nova tentativa (retry) via Exponential Backoff
            try:
                raise self.retry()
            except MaxRetriesExceededError:
                print(f"[WORKER] ❌ Limite máximo de tentativas esgotado para: {nome_padronizado}")
                report.status_compliance = "Vermelho"
                db.commit()
                return False
        else:
            link_encontrado = video_drive.get('webViewLink')
            md5_hash = video_drive.get('md5Checksum', 'N/A')
            size_bytes = int(video_drive.get('size', 0))
            
            # Trava de Integridade SRE: Vídeo menos de 100MB é possivelmente corrompido
            if size_bytes < 100 * 1024 * 1024:
                print(f"[WORKER] ⚠️ Vídeo possivelmente corrompido ou incompleto: {size_bytes / (1024*1024):.2f} MB")
                report.status_compliance = "Pendente"
                obs_atual = report.observacoes or ""
                if "Falha de Integridade: Arquivo Corrompido ou Incompleto (Menos de 100MB)" not in obs_atual:
                    report.observacoes = obs_atual + "\nFalha de Integridade: Arquivo Corrompido ou Incompleto (Menos de 100MB)"
                db.commit()
                try:
                    raise self.retry()
                except MaxRetriesExceededError:
                    report.status_compliance = "Vermelho"
                    db.commit()
                    return False
            else:
                report.video_link = link_encontrado
                report.status_compliance = "Verde"
                report.md5_checksum = md5_hash
                
                # Armazena o Hash no log de observações caso exigido para transição binária futura
                obs_atual = report.observacoes or ""
                if md5_hash not in obs_atual:
                    report.observacoes = obs_atual + f"\n[SRE] Arquivo Íntegro. Hash MD5: {md5_hash}"
                
                print(f"[WORKER] ✅ Vídeo encontrado e validado: {video_drive.get('name')} -> {link_encontrado}")

        db.commit()
        return True

    except Exception as e:
        print(f"[WORKER] ❌ Falha na tarefa: {str(e)}")
        db.rollback()
        # Exception será engolida pelo autoretry_for ou retentada, se rate limits (429/423)
        raise e
    finally:
        db.close()

@celery_app.task(name="heartbeat_sistema")
def heartbeat_sistema():
    print("[WORKER] Heartbeat: Sistema de automação operacional ativo.")
    return "OK"

@celery_app.task(name="sincronizacao_noturna_drive")
def sincronizacao_noturna_drive():
    """
    Varredura (Cron): Busca no banco todos os relatórios 'Pendentes'
    e re-dispara a tarefa individual de verificação.
    """
    print("[WORKER] 🌙 Iniciando Sincronização Noturna do Drive...")
    db = SessionLocal()
    try:
        pendentes = (
            db.query(ClassReport)
            .filter(ClassReport.status_compliance == "Pendente")
            .filter(ClassReport.nome_ficheiro_gerado != None)
            .all()
        )
        
        for p in pendentes:
            verificar_compliance_drive.delay(str(p.id), p.nome_ficheiro_gerado)
            
        print(f"[WORKER] ✅ Sincronização Noturna: {len(pendentes)} relatórios(s) re-agendado(s) para fila de retry.")
        return len(pendentes)
    except Exception as e:
        print(f"[WORKER] ❌ Erro na Sincronização Noturna: {str(e)}")
        return 0
    finally:
        db.close()