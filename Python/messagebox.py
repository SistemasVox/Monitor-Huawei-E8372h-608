import tkinter as tk
from tkinter import messagebox

def main():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo("Informação", "Esta é uma caixa de diálogo de informação.")
    messagebox.showwarning("Aviso", "Esta é uma caixa de diálogo de aviso.")
    messagebox.showerror("Erro", "Esta é uma caixa de diálogo de erro.")
    
    response = messagebox.askquestion("Pergunta", "Você gostaria de continuar?")
    if response == 'yes':
        messagebox.showinfo("Resposta", "Você escolheu 'Sim' na caixa de diálogo de pergunta.")
    else:
        messagebox.showinfo("Resposta", "Você escolheu 'Não' na caixa de diálogo de pergunta.")
    
    response = messagebox.askokcancel("Confirmação", "Deseja confirmar?")
    if response:
        messagebox.showinfo("Resposta", "Você escolheu 'OK' na caixa de diálogo de confirmação.")
    else:
        messagebox.showinfo("Resposta", "Você escolheu 'Cancelar' na caixa de diálogo de confirmação.")
    
    response = messagebox.askyesno("Escolha", "Você prefere 'Sim' ou 'Não'?")
    if response:
        messagebox.showinfo("Resposta", "Você escolheu 'Sim' na caixa de diálogo de escolha.")
    else:
        messagebox.showinfo("Resposta", "Você escolheu 'Não' na caixa de diálogo de escolha.")
    
    response = messagebox.askretrycancel("Repetir", "Deseja tentar novamente?")
    if response:
        messagebox.showinfo("Resposta", "Você escolheu 'Tentar Novamente' na caixa de diálogo de repetição.")
    else:
        messagebox.showinfo("Resposta", "Você escolheu 'Cancelar' na caixa de diálogo de repetição.")

    root.destroy()

main()
