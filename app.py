from fastapi import FastAPI, HTTPException
import pandas as pd
from twilio.rest import Client
import os
from dotenv import load_dotenv

app = FastAPI()

# Carrega variáveis de ambiente
load_dotenv()

# Configuração segura do Twilio
client = Client(os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN'))


@app.get("/")
def home():
    return {"message": "Bem-vindo ao sistema de monitoramento de metas!"}


@app.post("/verificar-meta/{mes}")
async def verificar_meta(mes: str):
    try:
        # Verifica se arquivo existe
        if not os.path.exists(f'{mes}.xlsx'):
            raise HTTPException(
                status_code=404, detail=f"Arquivo {mes}.xlsx não encontrado")

        tabela_vendas = pd.read_excel(f'{mes}.xlsx')

        # Verifica colunas necessárias
        if 'Vendas' not in tabela_vendas or 'Vendedor' not in tabela_vendas:
            raise HTTPException(
                status_code=400, detail="Arquivo Excel não contém colunas necessárias")

        if (tabela_vendas['Vendas'] > 55000).any():
            vendedor = tabela_vendas.loc[tabela_vendas['Vendas']
                                         > 55000, 'Vendedor'].values[0]
            vendas = tabela_vendas.loc[tabela_vendas['Vendas']
                                       > 55000, 'Vendas'].values[0]

            # Envia SMS
            message = client.messages.create(
                to=os.getenv('SEU_NUMERO'),
                from_=os.getenv('TWILIO_NUMBER'),
                body=f'✅ Meta batida em {mes.capitalize()}\nVendedor: {vendedor}\nValor: R${vendas:,.2f}'
            )

            return {
                "status": "sucesso",
                "mes": mes,
                "vendedor": vendedor,
                "vendas": float(vendas),
                "sid": message.sid
            }

        return {"status": "info", "mensagem": f"Nenhum vendedor bateu a meta em {mes}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
