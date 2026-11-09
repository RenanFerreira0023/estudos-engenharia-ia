"""Prepara o índice real de políticas uma vez; não executa atendimento."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from auto_super_parts.atendimento_memoria import criar_embeddings
from auto_super_parts.rag_politicas import preparar_indice


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--real',action='store_true',help='Autoriza vetorização real com a configuração OpenAI do projeto.')
    parser.add_argument('--saida',type=Path)
    parser.add_argument('--arquivo-env',type=Path)
    args=parser.parse_args()
    if not args.real:
        parser.exit(2,'Use --real para preparar com embeddings reais; testes offline usam fixtures em pastas temporárias.\n')
    # EMBEDDINGS cria o artefato separadamente; o atendimento só o carrega.
    r=preparar_indice(criar_embeddings(args.arquivo_env),pasta=args.saida,origem_embedding='API real OpenAI')
    print('Índice preparado:',r['quantidade'],'documentos;',r['modelo_embedding'],'dimensão',r['dimensao'])


if __name__=='__main__':
    main()
