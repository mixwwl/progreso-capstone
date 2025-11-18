// carrito.js
document.addEventListener('DOMContentLoaded', function() {
    // Efectos de hover para productos del carrito
    const productosCarrito = document.querySelectorAll('.producto-carrito');
    
    productosCarrito.forEach(producto => {
        producto.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        producto.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Confirmación antes de acciones importantes
    const formsEliminar = document.querySelectorAll('form[action*="eliminar"]');
    formsEliminar.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('¿Estás seguro de que quieres eliminar este producto del carrito?')) {
                e.preventDefault();
            }
        });
    });

    // Efecto visual al actualizar cantidades
    const formsCantidad = document.querySelectorAll('.form-cantidad');
    formsCantidad.forEach(form => {
        form.addEventListener('submit', function(e) {
            const boton = e.submitter;
            const textoOriginal = boton.textContent;
            
            // Feedback visual
            if (boton.name === 'accion') {
                boton.style.backgroundColor = '#ffc107';
                boton.style.color = '#212529';
                
                setTimeout(() => {
                    boton.style.backgroundColor = '';
                    boton.style.color = '';
                }, 500);
            }
        });
    });

    // Animación para el resumen sticky
    const resumenCard = document.querySelector('.resumen-card');
    if (resumenCard) {
        window.addEventListener('scroll', function() {
            const scrollY = window.scrollY;
            if (scrollY > 100) {
                resumenCard.style.transform = 'translateY(-5px)';
                resumenCard.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
            } else {
                resumenCard.style.transform = 'translateY(0)';
                resumenCard.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
            }
        });
    }

    // Mensaje de carga para el botón de pago
    const btnPagar = document.querySelector('.btn-pagar');
    if (btnPagar) {
        btnPagar.addEventListener('click', function(e) {
            e.preventDefault();
            const textoOriginal = this.textContent;
            this.textContent = 'Procesando...';
            this.style.backgroundColor = '#ffc107';
            this.style.color = '#212529';
            
            setTimeout(() => {
                alert('Funcionalidad de pago en desarrollo');
                this.textContent = textoOriginal;
                this.style.backgroundColor = '';
                this.style.color = '';
            }, 2000);
        });
    }
});