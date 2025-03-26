from fastapi import FastAPI, HTTPException
import pandas as pd
from twilio.rest import Client
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from typing import List, Dict

# Configuração inicial
app = FastAPI(
    title="API de Monitoramento de Metas",
    description="Sistema para verificar metas de vendas e enviar notificações por SMS",
    version="1.0.0"
)

# Configuração de logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Carrega variáveis de ambiente
load_dotenv()

# Configuração segura do Twilio
try:
    client = Client(
        os.getenv('TWILIO_ACCOUNT_SID'),
        os.getenv('TWILIO_AUTH_TOKEN')
    )
except Exception as e:
    logging.error(f"Erro na configuração do Twilio: {str(e)}")
    raise RuntimeError("Falha na configuração do serviço de SMS")

# Constantes
PASTA_DADOS = Path('dados')
META_VENDAS = 55000


@app.get("/", summary="Endpoint inicial")
def home():
    """Endpoint raiz da API"""
    return {"message": "Bem-vindo ao sistema de monitoramento de metas!"}


@app.post(
    "/verificar-meta/{mes}",
    response_model=Dict,
    responses={
        200: {"description": "Meta verificada com sucesso"},
        400: {"description": "Requisição inválida"},
        404: {"description": "Arquivo não encontrado"},
        422: {"description": "Dados inválidos no arquivo"},
        500: {"description": "Erro interno no servidor"}
    },
    summary="Verifica se vendedores bateram a meta",
    description="Analisa planilha Excel do mês especificado e notifica por SMS caso a meta seja batida"
)
async def verificar_meta(mes: str):
    """
    Verifica as vendas de um determinado mês e envia SMS se a meta for batida

    - **mes**: Mês a ser analisado (ex: 'janeiro', 'fevereiro')
    """
    try:
        # Validação do parâmetro
        if not mes.isalpha():
            raise HTTPException(
                status_code=400,
                detail="Nome do mês deve conter apenas letras"
            )

        # Verificação do arquivo
        arquivo = PASTA_DADOS / f'{mes.lower()}.xlsx'
        if not arquivo.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Arquivo {mes}.xlsx não encontrado na pasta 'dados'"
            )

        # Leitura do arquivo
        try:
            tabela_vendas = pd.read_excel(arquivo)
        except Exception as e:
            logging.error(f"Erro ao ler arquivo {arquivo}: {str(e)}")
            raise HTTPException(
                status_code=422,
                detail=f"Erro ao processar o arquivo Excel: {str(e)}"
            )

        # Validação dos dados
        if tabela_vendas.empty:
            raise HTTPException(
                status_code=422,
                detail="Arquivo Excel está vazio"
            )

        colunas_necessarias = {'Vendas', 'Vendedor'}
        if not colunas_necessarias.issubset(tabela_vendas.columns):
            raise HTTPException(
                status_code=422,
                detail=f"Arquivo Excel deve conter as colunas: {', '.join(colunas_necessarias)}"
            )

        # Verificação de valores nulos
        if tabela_vendas['Vendas'].isnull().any():
            raise HTTPException(
                status_code=422,
                detail="Existem valores nulos na coluna 'Vendas'"
            )

        # Filtra vendedores que bateram a meta
        vendedores_meta = tabela_vendas[tabela_vendas['Vendas'] > META_VENDAS]

        if not vendedores_meta.empty:
            # Prepara mensagem detalhada
            mensagem_sms = f"🚀 Metas batidas em {mes.capitalize()}:\n\n"
            for _, row in vendedores_meta.iterrows():
                mensagem_sms += f"• {row['Vendedor']}: R${row['Vendas']:,.2f}\n"

            # Envio de SMS
            try:
                message = client.messages.create(
                    to=os.getenv('SEU_NUMERO'),
                    from_=os.getenv('TWILIO_NUMBER'),
                    body=mensagem_sms
                )
                logging.info(f"SMS enviado para {mes}. SID: {message.sid}")
            except Exception as e:
                logging.error(f"Erro ao enviar SMS: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao enviar notificação por SMS"
                )

            # Prepara resposta
            resultado = {
                "status": "sucesso",
                "mes": mes,
                "vendedores": [
                    {
                        "nome": row['Vendedor'],
                        "vendas": float(row['Vendas'])
                    } for _, row in vendedores_meta.iterrows()
                ],
                "total_vendedores": len(vendedores_meta),
                "sid_sms": message.sid if 'message' in locals() else None
            }

            return resultado

        return {
            "status": "info",
            "mensagem": f"Nenhum vendedor bateu a meta de R${META_VENDAS:,.2f} em {mes}"
        }

    except HTTPException:
        raise  # Re-lança exceções HTTP já tratadas
    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocorreu um erro inesperado no servidor"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
