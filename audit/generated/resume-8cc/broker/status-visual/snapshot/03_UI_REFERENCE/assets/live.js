/* Presentation-only interactions. No backend, secret access or business operations. */
const dialog = document.querySelector('dialog');
let invoker;
let menuInvoker;
function openMenu(source) {
  menuInvoker=source;
  const menu=document.querySelector('.sample-menu');
  menu.classList.add('open');
  document.querySelector('[data-menu]').setAttribute('aria-expanded','true');
  menu.querySelector('button').focus();
}
function closeMenu() {
  document.querySelector('.sample-menu').classList.remove('open');
  document.querySelector('[data-menu]').setAttribute('aria-expanded','false');
  menuInvoker?.focus();
}
function explain(text, source) { invoker=source; dialog.querySelector('p').textContent=text; dialog.showModal(); }
document.addEventListener('click', event => {
  const button=event.target.closest('button'); if(!button) return;
  if(button.dataset.close!==undefined){dialog.close();return;}
  if(button.dataset.menu!==undefined){const menu=document.querySelector('.sample-menu');if(menu.classList.contains('open'))closeMenu();else openMenu(button);return;}
  if(button.dataset.zoom){const svg=document.querySelector('.graph>svg');let scale=Number(svg.dataset.scale||1);scale=button.dataset.zoom==='fit'?1:Math.max(.7,Math.min(1.5,scale+(button.dataset.zoom==='in'?.1:-.1)));svg.dataset.scale=scale;svg.querySelector('.topology-content').setAttribute('transform',`translate(${320*(1-scale)} ${140*(1-scale)}) scale(${scale})`);return;}
  explain(button.dataset.help||document.body.dataset.demoExplanation,button);
});
dialog.addEventListener('close',()=>invoker?.focus());
document.querySelector('.graph')?.addEventListener('contextmenu',event=>{event.preventDefault();openMenu(event.currentTarget);});
document.addEventListener('keydown',event=>{
 if(dialog.open)return;
 const menu=document.querySelector('.sample-menu');
 if(event.shiftKey&&event.key==='F10'&&event.target.closest('.graph')){event.preventDefault();openMenu(event.target.closest('.graph'));}
 if(menu?.classList.contains('open')){
  const buttons=[...menu.querySelectorAll('button')];let i=buttons.indexOf(document.activeElement);
  if(event.key==='Escape'){closeMenu();}
  if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();i=event.key==='Home'?0:event.key==='End'?buttons.length-1:(i+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[i].focus();}
 }
});
