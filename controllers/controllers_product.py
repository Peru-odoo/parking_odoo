# -*- coding: utf-8 -*-
from odoo import http
import uuid


def create_product_move_history(state, product_id, location_id, location_dest_id, epc):
    stock_move_history = http.request.env["stock.move.line"].sudo().create(
        {'reference': state,
         'product_id': product_id,
         'reserved_uom_qty': 1.0,
         'lot_name': epc,
         'location_id': location_id,
         'location_dest_id': location_dest_id,
         'qty_done': 1.0,
         'company_id': 1})


def find_location_empty():
    # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
    locations_empty = http.request.env["stock.location"].sudo().search([
        ('state', '=', 'empty')])

    # Tìm danh vị trí trống đầu tiên trong danh sách
    for location_empty in locations_empty:
        # Có nhiều bãi xe nên tìm bãi xe của mình
        # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
        location = location_empty.complete_name.split('/')
        # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
        # BX\A\A1 or BX\B\B2
        if 'BX' in location and len(location) > 2:
            # Cập nhật vị trí đã đầy
            # Cập nhật vị trí đã đầy
            location_empty.write({'state': 'full'})
            return location_empty.id
    return -1

class ControllerProduct(http.Controller):

    @http.route('/parking/post/check_product', website=False, csrf=False, type='json', methods=['POST'], auth='public')
    def parking_create_product(self, **kw):
        serial_ids = http.request.env["stock.lot"].sudo().search(
            [('name', '=', kw['sEPC'])])

        if not serial_ids:
            password_tag = uuid.uuid4().hex[:8] + "\0"
            product = http.request.env["product.product"].sudo().create({
                'name': "xe_["+kw['sEPC']+"]",
                'tracking': 'serial',
                'password': password_tag,
            })
            http.request.env["stock.lot"].sudo().create({
                'name': kw['sEPC'],
                'product_id': product.id,
                "company_id": 1
            })
            # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
            locations_empty = http.request.env["stock.location"].sudo().search([
                ('state', '=', 'empty')])

            # Tìm danh vị trí trống đầu tiên trong danh sách
            for location_empty in locations_empty:
               # Có nhiều bãi xe nên tìm bãi xe của mình
               # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
                location = location_empty.complete_name.split('/')
                # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
                # BX\A\A1 or BX\B\B2
                if 'BX' in location and len(location) > 2:
                   # Cập nhật vị trí đã đầy
                    location_empty.write({'state': 'full'})
                    create_product_move_history(
                        "BX/IN", product.id, 4, location_empty.id, kw['sEPC'])
                    break

            return password_tag
        else:
            return serial_ids.product_id.password

    @http.route('/parking/post/move_history', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post(self, **kw):
        # lấy danh sách ID của thẻ trong kho move history
        product_move_list = http.request.env["stock.move.line"].sudo().search(
            [('lot_name', '=', kw['sEPC'])])

        # tìm ID lớn nhất (thời gian đi vào gần nhất)
        max_object = max(product_move_list, key=lambda x: x['id'])
        # lấy thông tin của ID lớn nhất
        # kiểm tra ra hay vào nếu ra thì thêm vào và ngược lại

        if 'OUT' in max_object.reference:
            location_empty_id = find_location_empty()
            if location_empty_id == -1:
                return "BAI XE FULL"
            create_product_move_history(
                "BX/IN", max_object.product_id.id, 4, location_empty_id(), kw['sEPC'])
            return "Da Vao"
        else:
            location = http.request.env["stock.location"].sudo().search(
                [('id', '=', max_object.location_dest_id.id)])
            location.write({'state': 'empty'})

            create_product_move_history(
                "BX/OUT", max_object.product_id.id, max_object.location_dest_id.id, 5, kw['sEPC'])
            return "Da Ra"

    @http.route('/parking/post/in/move_history', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_in_move_history(self, **kw):
        # lấy danh sách ID của thẻ trong kho move history
        product_move_list = http.request.env["stock.move.line"].sudo().search(
            [('lot_name', '=', kw['sEPC'])])

        # tìm ID lớn nhất (thời gian đi vào gần nhất)
        max_object = max(product_move_list, key=lambda x: x['id'])
        # lấy thông tin của ID lớn nhất
        # kiểm tra ra hay vào nếu ra thì thêm vào và ngược lại

        if 'OUT' in max_object.reference:
            location_empty_id = find_location_empty()
            if location_empty_id == -1:
                return "BAI XE FULL"
            create_product_move_history(
                "BX/IN", max_object.product_id.id, 4, location_empty_id, kw['sEPC'])
            return "Da Vao"
        else:
            return "Xe da vao roi"

    @http.route('/parking/post/out/move_history', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_out_move_history(self, **kw):
        # lấy danh sách ID của thẻ trong kho move history
        product_move_list = http.request.env["stock.move.line"].sudo().search(
            [('lot_name', '=', kw['sEPC'])])

        # tìm ID lớn nhất (thời gian đi vào gần nhất)
        max_object = max(product_move_list, key=lambda x: x['id'])
        # lấy thông tin của ID lớn nhất
        # kiểm tra ra hay vào nếu ra thì thêm vào và ngược lại

        if 'IN' in max_object.reference:
            location = http.request.env["stock.location"].sudo().search(
                [('id', '=', max_object.location_dest_id.id)])
            location.write({'state': 'empty'})

            create_product_move_history(
                "BX/OUT", max_object.product_id.id, max_object.location_dest_id.id, 5, kw['sEPC'])
            return "Da Ra"
        else:
            return "Xe da Ra roi"
