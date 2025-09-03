from flask import Blueprint, request, jsonify, session, g
from orders.models.order_model import Orders
from db.db import db
from datetime import datetime
import requests

order_controller = Blueprint('order_controller', __name__)

@order_controller.route('/api/orders', methods=['GET'])
def get_orders():
    print("listado de ordenes")
    
    orders = Orders.query.all()
    result = []
    for order in orders:
        result.append({
            'id': order.id, 
            'userName': order.userName, 
            'userEmail': order.userEmail, 
            'saleTotal': float(order.saleTotal) if order.saleTotal else None,
            'date': order.date.isoformat() if order.date else None
        })
    return jsonify(result)

@order_controller.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    print("obteniendo orden")
    order = Orders.query.get_or_404(order_id)
    return jsonify({
        'id': order.id, 
        'userName': order.userName, 
        'userEmail': order.userEmail, 
        'saleTotal': float(order.saleTotal) if order.saleTotal else None,
        'date': order.date.isoformat() if order.date else None
    })

@order_controller.route('/api/orders', methods=['POST'])
def create_order():
    """
    Endpoint para crear una nueva orden.
    Recibe un JSON con una lista de productos con sus respectivos IDs y cantidades.
    Toma la información de usuario desde sesión.
    Calcula el total de la venta, verifica la disponibilidad de los productos y
    actualiza el inventario llamando al endpoint de actualización de productos.
    
    Args:
        None
    
    Returns:
        JSON: Un mensaje de confirmación si la orden se crea correctamente,
        o un mensaje de error con el código de estado HTTP apropiado.
    """
    print("creando orden")
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No se proporcionaron datos'}), 400
    
    # Extract user information from session (prioritized) or fallback to request
    user_name = session.get('username')
    user_email = session.get('email')
    
    # Fallback to request data for backward compatibility
    if not user_name or not user_email:
        if 'user' in data:
            user_data = data.get('user', {})
            user_name = user_data.get('name', '')
            user_email = user_data.get('email', '')
        else:
            user_name = data.get('userName', '')
            user_email = data.get('userEmail', '')
    
    # Validate user information
    if not user_name or not user_email:
        return jsonify({'message': 'Información de usuario inválida. Asegúrese de estar autenticado.'}), 400
    
    # Extract and validate products - now required
    products = data.get('products')
    if not products or not isinstance(products, list):
        return jsonify({'message': 'Falta o es inválida la información de los productos'}), 400
    
    try:
        # Calculate total and validate product availability
        sale_total, processed_products = _calculate_order_total(products)
        
        # Update inventory and create order in transaction
        order_result = _process_order_transaction(
            user_name, user_email, sale_total, processed_products, data
        )
        
        return jsonify(order_result), 201
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except requests.RequestException as e:
        return jsonify({'message': f'Error de comunicación con microservicio: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'message': f'Error inesperado al procesar la orden: {str(e)}'}), 500



def _calculate_order_total(products):
    """
    Calculates order total and validates product availability.
    
    Args:
        products: List of product items with id and quantity
        
    Returns:
        tuple: (sale_total, processed_products)
        
    Raises:
        ValueError: If products are invalid or insufficient stock
        requests.RequestException: If product service unavailable
    """
    sale_total = 0
    processed_products = []
    
    for product_item in products:
        product_id = product_item.get('id')
        quantity = int(product_item.get('quantity', 0))
        
        if not product_id or quantity <= 0:
            continue
        
        # Fetch current product data from products microservice
        response = requests.get(f'http://192.168.80.3:5003/api/products/{product_id}')
        if response.status_code != 200:
            raise ValueError(f'Producto con ID {product_id} no encontrado')
        
        product_data = response.json()
        current_stock = int(product_data.get('quantity', 0))
        price = float(product_data.get('price', 0))
        product_name = product_data.get('name', f'Producto {product_id}')
        
        # Validate stock availability
        if current_stock < quantity:
            raise ValueError(
                f'Stock insuficiente para {product_name}. '
                f'Stock disponible: {current_stock}, solicitado: {quantity}'
            )
        
        # Calculate subtotal
        subtotal = quantity * price
        sale_total += subtotal
        
        # Store product info for inventory update
        processed_products.append({
            'id': product_id,
            'name': product_name,
            'quantity': quantity,
            'price': price,
            'current_stock': current_stock,
            'subtotal': subtotal
        })
    
    if not processed_products:
        raise ValueError('No hay productos válidos en la orden')
    
    return sale_total, processed_products


def _process_order_transaction(user_name, user_email, sale_total, processed_products, data):
    """
    Processes order transaction: updates inventory and creates order.
    
    Args:
        user_name: Customer name
        user_email: Customer email  
        sale_total: Total order amount
        processed_products: List of validated products
        data: Original request data
        
    Returns:
        dict: Order creation result
        
    Raises:
        Exception: If transaction fails
    """
    try:
        # Update inventory for each product
        for product in processed_products:
            new_stock = product['current_stock'] - product['quantity']
            
            # Call products microservice to update inventory
            update_response = requests.put(
                f'http://192.168.80.3:5003/api/products/{product["id"]}',
                json={
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': new_stock
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if update_response.status_code != 200:
                raise Exception(f'Error al actualizar inventario del producto {product["name"]}')
        
        # Create the order record
        date_obj = datetime.utcnow()
        if 'date' in data and data['date']:
            try:
                date_obj = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except:
                pass
        
        new_order = Orders(
            userName=user_name,
            userEmail=user_email,
            saleTotal=sale_total,
            date=date_obj
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # Prepare detailed response
        return {
            'message': 'Orden creada exitosamente',
            'order': {
                'orderId': new_order.id,
                'userName': user_name,
                'userEmail': user_email,
                'products': [
                    {
                        'name': p['name'],
                        'quantity': p['quantity'],
                        'price': p['price'],
                        'subtotal': p['subtotal']
                    } for p in processed_products
                ],
                'saleTotal': sale_total,
                'date': date_obj.isoformat()
            }
        }
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f'Error al procesar la orden: {str(e)}')

@order_controller.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    print("actualizando orden")
    order = Orders.query.get_or_404(order_id)
    data = request.json
    
    # Handle missing fields gracefully
    order.userName = data.get('userName', order.userName)
    order.userEmail = data.get('userEmail', order.userEmail)
    order.saleTotal = data.get('saleTotal', order.saleTotal)
    
    if 'date' in data and data['date']:
        try:
            order.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        except:
            pass
    
    db.session.commit()
    return jsonify({'message': 'Order updated successfully'})

@order_controller.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    print("eliminando orden")
    order = Orders.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order deleted successfully'})