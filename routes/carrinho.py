from flask import Blueprint, session, jsonify, flash, redirect, url_for
from models import db, Marmita, CarrinhoItem
from utilities import get_user_carrinho_db # Importar funções úteis

carrinho_bp = Blueprint('carrinho', __name__)

