/*
 * PT: Aplica o tema escolhido pelo visitante antes da primeira pintura, para
 *     a página não piscar no tema errado. É um script comum, síncrono, no
 *     <head>, e vem do próprio site, como pede a política de segurança. A
 *     chave é a mesma de src/componentes/controle-de-tema.js. Sem escolha
 *     guardada, ou sem acesso ao armazenamento, não faz nada, e o CSS segue
 *     o sistema.
 *
 * EN: Applies the stored theme before first paint so the page never flashes
 *     the wrong theme. Same key as src/componentes/controle-de-tema.js.
 */
(() => {
  try {
    const escolha = localStorage.getItem("credito-pj:tema");
    if (escolha === "claro" || escolha === "escuro") {
      document.documentElement.dataset.tema = escolha;
    }
  } catch {
    // PT: sem armazenamento, vale o sistema / EN: no storage, follow the system
  }
})();
