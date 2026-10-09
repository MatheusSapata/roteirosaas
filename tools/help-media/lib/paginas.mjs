// Páginas da agência de demonstração (usadas por seed.mjs e para restaurar uma página
// que um roteiro alterou).
export const dia = n => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
};

export function paginas(f, formId) {
  const header = links => ({ type: 'header', enabled: true, anchorId: 'menu', mode: 'transparent', links, actionType: 'contact', contactLabel: 'Falar no WhatsApp', contactType: 'whatsapp', contactValue: '48999990000', stickyEnabled: true });
  const footer = { type: 'agency_footer', enabled: true, showCadastur: true };
  return [
    {
      title: 'Jalapão 6 dias', slug: 'jalapao-6-dias', publish: true, principal: true,
      sections: [
        header([{ id: 'l1', label: 'Roteiro', targetType: 'section', target: 'roteiro' }, { id: 'l2', label: 'Preços', targetType: 'section', target: 'precos' }, { id: 'l3', label: 'Dúvidas', targetType: 'section', target: 'duvidas' }]),
        { type: 'hero', enabled: true, anchorId: 'inicio', layout: 'immersive', title: 'Jalapão 6 dias: fervedouros, dunas e cachoeiras', subtitle: 'Saída de Palmas com guia credenciado, pousadas charmosas e veículo 4x4.', backgroundImage: f.dunas, chips: ['Hospedagem inclusa', 'Guia credenciado', 'Veículo 4x4', 'Grupos pequenos'], departureDate: dia(46), returnDate: dia(51), ctaLabel: 'Quero reservar', ctaMode: 'section', ctaSectionId: 'precos' },
        { type: 'countdown', enabled: true, headingLabel: 'Oferta por tempo limitado', anchorId: 'oferta', label: 'Condição de lançamento termina em breve', countdownMode: 'fixed', targetDate: `${dia(5)}T23:59:00`, layout: 'cards' },
        { type: 'story', enabled: true, anchorId: 'sobre', layout: 'gallery', imagePosition: 'right', badge: 'Sobre a viagem', title: 'Seis dias no coração do Tocantins', subtitle: 'Fervedouros de águas cristalinas, as dunas douradas ao pôr do sol e a Cachoeira da Velha. Grupos de até 12 pessoas, com tempo para aproveitar cada parada sem pressa.', images: [f.dunas, f.rio], ctaEnabled: true, ctaLabel: 'Ver o roteiro', ctaMode: 'section', ctaSectionId: 'roteiro' },
        { type: 'reasons', enabled: true, headingLabel: 'Por que escolher', anchorId: 'diferenciais', title: 'Por que viajar com a Rota Sul', subtitle: 'O que está incluso e faz diferença.', iconMode: 'icon', items: [{ icon: 'icon:bed', title: 'Pousadas charmosas', description: 'Cinco noites com café da manhã.' }, { icon: 'icon:guide', title: 'Guia credenciado', description: 'Quem conhece o Jalapão de verdade.' }, { icon: 'icon:bus', title: 'Veículo 4x4', description: 'Traslados e passeios sem preocupação.' }, { icon: 'icon:shield', title: 'Seguro viagem', description: 'Tranquilidade do começo ao fim.' }] },
        { type: 'itinerary', enabled: true, headingLabel: 'Itinerário', anchorId: 'roteiro', layout: 'journey', title: 'Roteiro dia a dia', subtitle: 'O que acontece em cada dia.', startDate: dia(46), days: [
          { day: 'Dia 1', title: 'Chegada em Palmas', description: 'Recepção no aeroporto e jantar de boas-vindas.', image: f.cidade },
          { day: 'Dia 2', title: 'Cachoeira da Velha', description: 'Banho de rio e almoço regional.', image: f.rio },
          { day: 'Dia 3', title: 'Dunas douradas', description: 'Trilha leve e pôr do sol nas dunas.', image: f.dunas },
          { day: 'Dia 4', title: 'Fervedouros', description: 'Três fervedouros com flutuação.' },
          { day: 'Dia 5', title: 'Serra do Espírito Santo', description: 'Subida com vista panorâmica.', image: f.serra },
          { day: 'Dia 6', title: 'Retorno', description: 'Traslado para o aeroporto de Palmas.' },
        ] },
        { type: 'gallery', enabled: true, headingLabel: 'Galeria', anchorId: 'fotos', layout: 'mosaic', title: 'Fotos da última saída', images: [f.dunas, f.rio, f.serra, f.cidade, f.praia] },
        { type: 'prices', enabled: true, headingLabel: 'Investimento', anchorId: 'precos', layout: 'columns', title: 'Escolha seu pacote', subtitle: 'Valores por pessoa, em até 10x sem juros.', ctaLabel: 'Reservar', items: [
          { title: 'Quarto duplo', price: 4890, priceLabel: 'por pessoa', currency: 'BRL', ctaLink: 'https://wa.me/5548999990000' },
          { title: 'Quarto triplo', price: 4590, priceLabel: 'por pessoa', currency: 'BRL', highlight: true, badge: 'Mais vendido', ctaLink: 'https://wa.me/5548999990000' },
          { title: 'Quarto individual', price: 6290, priceLabel: 'por pessoa', currency: 'BRL', ctaLink: 'https://wa.me/5548999990000' },
        ] },
        { type: 'testimonials', enabled: true, headingLabel: 'Depoimentos', anchorId: 'depoimentos', layout: 'grid', title: 'Quem já foi conta', items: [
          { name: 'Juliana Prado', role: 'Saída de julho', text: 'Tudo muito bem organizado. O guia fez toda a diferença.', rating: 5 },
          { name: 'Ricardo Mendes', role: 'Saída de maio', text: 'As pousadas eram ótimas e o grupo pequeno deixou tudo mais leve.', rating: 5 },
          { name: 'Camila Rocha', role: 'Saída de setembro', text: 'O pôr do sol nas dunas vale a viagem inteira.', rating: 5 },
        ] },
        { type: 'faq', enabled: true, headingLabel: 'FAQ', anchorId: 'duvidas', layout: 'accordion', title: 'Dúvidas frequentes', items: [
          { question: 'O que está incluso?', answer: 'Hospedagem com café, guia, veículo 4x4, ingressos dos atrativos e seguro viagem.' },
          { question: 'Posso parcelar?', answer: 'Sim, em até 10x sem juros no cartão.' },
          { question: 'Qual o tamanho do grupo?', answer: 'Até 12 pessoas por saída.' },
        ] },
        ...(formId ? [{ type: 'internal_form', enabled: true, anchorId: 'contato', title: 'Entre na lista de espera', subtitle: 'Avisamos você primeiro quando abrir a próxima saída.', formId: String(formId), backgroundType: 'solid', alignment: 'center' }] : []),
        { type: 'cta', enabled: true, anchorId: 'chamada', label: 'Pronto para o Jalapão?', description: 'Fale com a gente e garanta sua vaga.', ctaEnabled: true, ctaText: 'Falar no WhatsApp', link: 'https://wa.me/5548999990000' },
        footer,
      ],
    },
    {
      title: 'Chile: Santiago e vinícolas', slug: 'chile-santiago-vinicolas', publish: true,
      sections: [
        { type: 'hero', enabled: true, layout: 'split', title: 'Santiago e as vinícolas do Vale do Maipo', subtitle: 'Sete dias entre a cidade, a cordilheira e as melhores vinícolas do Chile.', backgroundImage: f.vinhedo, chips: ['Aéreo incluso', 'Degustações', 'Traslados'], departureDate: dia(70), returnDate: dia(76), ctaLabel: 'Quero saber mais', ctaLink: 'https://wa.me/5548999990000' },
        { type: 'story', enabled: true, layout: 'gallery', imagePosition: 'left', badge: 'A viagem', title: 'Vinho, neve e cidade', subtitle: 'Três vinícolas com degustação guiada, um dia na cordilheira e tempo livre em Santiago.', images: [f.vinhedo, f.serra] },
        { type: 'prices', enabled: true, headingLabel: 'Investimento', anchorId: 'precos', layout: 'columns', title: 'Valores', ctaLabel: 'Reservar', items: [{ title: 'Pacote completo', price: 7490, priceLabel: 'por pessoa', currency: 'BRL', ctaLink: 'https://wa.me/5548999990000' }] },
        { type: 'links', enabled: true, headingLabel: 'Links', title: 'Outros roteiros', carouselEnabled: true, items: [
          { id: 'a', source: 'external', url: '/rotasul/jalapao-6-dias', image: f.dunas, title: 'Jalapão 6 dias', description: 'Fervedouros, dunas e cachoeiras.', buttonLabel: 'Ver roteiro', showPrice: true, pricePrefix: 'a partir de', priceValue: 'R$ 4.590', priceSuffix: 'por pessoa' },
          { id: 'b', source: 'external', url: '/rotasul/reveillon-porto-de-galinhas', image: f.praia, title: 'Réveillon em Porto de Galinhas', description: 'Virada na praia com tudo incluso.', buttonLabel: 'Ver roteiro', showDates: true, departureDate: dia(83), returnDate: dia(88) },
        ] },
        footer,
      ],
    },
    {
      title: 'Bonito em família', slug: 'bonito-em-familia', publish: false,
      sections: [
        { type: 'hero', enabled: true, layout: 'card', title: 'Bonito em família', subtitle: 'Flutuação, grutas e cachoeiras para todas as idades.', backgroundImage: f.rio, chips: ['Crianças até 6 anos grátis'], ctaLabel: 'Quero ir', ctaLink: 'https://wa.me/5548999990000' },
        { type: 'reasons', enabled: true, headingLabel: 'Por que escolher', title: 'Feito para famílias', iconMode: 'icon', items: [{ icon: 'icon:bed', title: 'Quartos família' }, { icon: 'icon:guide', title: 'Passeios leves' }, { icon: 'icon:shield', title: 'Seguro incluso' }] },
        footer,
      ],
    },
    {
      title: 'Aula gratuita: planejando o Jalapão', slug: 'aula-jalapao', publish: true,
      sections: [
        { type: 'video_vsl', enabled: true, title: 'Assista antes de garantir sua vaga', subtitle: 'Em 12 minutos, tudo o que você precisa saber para planejar o Jalapão.', videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', thumbnailUrl: f.dunas, videoAspectRatio: 'horizontal', progressBarEnabled: true, unlockAfterSeconds: 300, unlockAction: 'both', ctaLabel: 'Quero minha vaga', ctaLink: 'https://wa.me/5548999990000' },
        { type: 'prices', enabled: true, headingLabel: 'Investimento', layout: 'columns', title: 'Condição para quem assistiu', ctaLabel: 'Reservar', items: [{ title: 'Jalapão 6 dias', price: 4590, priceLabel: 'por pessoa', currency: 'BRL', highlight: true, badge: 'Bônus da aula', ctaLink: 'https://wa.me/5548999990000' }] },
        footer,
      ],
    },
    {
      title: 'Réveillon em Porto de Galinhas', slug: 'reveillon-porto-de-galinhas', publish: true,
      sections: [
        { type: 'hero', enabled: true, layout: 'classic', title: 'Réveillon em Porto de Galinhas', subtitle: 'Cinco noites pé na areia, com festa da virada inclusa.', backgroundImage: f.praia, departureDate: dia(83), returnDate: dia(88), ctaLabel: 'Garantir minha vaga', ctaLink: 'https://wa.me/5548999990000' },
        { type: 'countdown', enabled: true, headingLabel: 'Oferta por tempo limitado', label: 'Lote promocional termina em', countdownMode: 'fixed', targetDate: `${dia(9)}T23:59:00`, layout: 'bar' },
        { type: 'prices', enabled: true, headingLabel: 'Investimento', layout: 'columns', title: 'Pacotes', ctaLabel: 'Reservar', items: [{ title: 'Pousada pé na areia', price: 5890, priceLabel: 'por pessoa', currency: 'BRL', ctaLink: 'https://wa.me/5548999990000' }, { title: 'Resort all inclusive', price: 8990, priceLabel: 'por pessoa', currency: 'BRL', highlight: true, badge: 'Tudo incluso', ctaLink: 'https://wa.me/5548999990000' }] },
        footer,
      ],
    },
  ];
}

