import pandas as pd
from twilio.rest import Client

# Your Account SID and Auth Token from console.twilio.com
account_sid = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
auth_token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
client = Client(account_sid, auth_token)

# Passo a passo de solução

# Abrir os 6 arquivos em Excel
lista_meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho']

for mes in lista_meses:
    tabelas_vendas = pd.read_excel(f'{mes}.xlsx')
    if (tabelas_vendas['Vendas'] > 55000).any():
        vendedor = tabelas_vendas.loc[tabelas_vendas['Vendas']
                                      > 55000, 'Vendedor'].values[0]
        vendas = tabelas_vendas.loc[tabelas_vendas['Vendas']
                                    > 55000, 'Vendas'].values[0]
        print(
            f'No mês {mes} alguém bateu a meta. Vendedor: {vendedor}, Vendas: {vendas}')
        message = client.messages.create(
            to="+55meunumero",
            from_="+17656130841",
            body=f'No mês {mes} alguém bateu a meta. Vendedor: {vendedor}, Vendas: {vendas}')
        print(message.sid)


# Para cada arquivo:

# Verificar se algum valor na coluna vendas daquele arquivo é maior que 55.000

# Se for maior que 55.000 => Enviar um sms com o Nome, o mês e as vendas do vendedor

# Casa não seja maior quue 55.000 não quero ffazer nada
