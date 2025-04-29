import flet as ft
import os
from PIL import Image
import io
from datetime import datetime

def main(page: ft.Page):
    page.title = "Convertidor de Imágenes a PDF"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 650
    page.window_resizable = True
    
    # Lista para almacenar las rutas de las imágenes seleccionadas
    selected_images = []
    
    # Variable para almacenar el índice que se está arrastrando
    dragging_index = None
    
    # Función para seleccionar imágenes
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            # Actualizar la lista de imágenes seleccionadas
            for f in e.files:
                selected_images.append(f.path)
            
            # Actualizar la visualización de imágenes
            update_image_list()
            
            # Habilitar el botón de convertir si hay imágenes seleccionadas
            convert_button.disabled = len(selected_images) == 0
            page.update()
    
    # Crear el selector de archivos
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)
    
    # Función para manejar el inicio del arrastre
    def on_drag_start(e, idx):
        nonlocal dragging_index
        dragging_index = idx
        e.control.content.border = ft.border.all(2, ft.colors.BLUE_ACCENT)
        page.update()
    
    # Función para manejar el final del arrastre
    def on_drag_end(e):
        nonlocal dragging_index
        dragging_index = None
        e.control.content.border = ft.border.all(1, ft.colors.GREY_400)
        page.update()
    
    # Función para aceptar el elemento arrastrado
    def on_will_accept(e, target_idx):
        # Mostrar indicador visual cuando el elemento puede ser soltado
        e.control.border = ft.border.all(2, ft.colors.GREEN_ACCENT) if e.data == "true" else ft.border.all(1, ft.colors.GREY_400)
        page.update()
    
    # Función para manejar el soltar el elemento
    def on_accept(e, target_idx):
        nonlocal dragging_index
        # Reiniciar el borde
        e.control.border = ft.border.all(1, ft.colors.GREY_400)
        
        # Mover la imagen a la nueva posición
        if dragging_index is not None and dragging_index != target_idx:
            # Guardar la imagen que estamos moviendo
            img = selected_images[dragging_index]
            
            # Eliminar la imagen de su posición original
            selected_images.pop(dragging_index)
            
            # Si el índice objetivo es mayor que el original, se reduce en 1 
            # porque hemos eliminado un elemento
            if target_idx > dragging_index:
                target_idx -= 1
            
            # Insertar la imagen en la nueva posición
            selected_images.insert(target_idx, img)
            
            # Actualizar la lista de imágenes
            update_image_list()
        
        dragging_index = None
        page.update()
    
    # Función para actualizar la lista de imágenes en la interfaz
    def update_image_list():
        images_grid.controls.clear()
        for idx, img_path in enumerate(selected_images):
            try:
                # Crear el contenido del contenedor de imagen
                img_content = ft.Column(
                    [
                        ft.Image(
                            src=img_path,
                            width=150,
                            height=150,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        ft.Text(os.path.basename(img_path), size=12),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    tooltip="Eliminar",
                                    on_click=lambda e, i=idx: remove_image(i)
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
                
                # Crear un contenedor Draggable para cada imagen
                img_drag = ft.Draggable(
                    group="images",
                    content=ft.Container(
                        content=img_content,
                        border=ft.border.all(1, ft.colors.GREY_400),
                        border_radius=10,
                        padding=10,
                        margin=5
                    ),
                    data=str(idx),  # Usamos el índice como dato para el arrastre
                )

                # Configurar los eventos después de crear el objeto
                img_drag.on_drag_start = lambda e, i=idx: on_drag_start(e, i)
                img_drag.on_drag_end = on_drag_end
                
                # Crear el DragTarget que envuelve al Draggable
                img_target = ft.DragTarget(
                    group="images",
                    content=img_drag,
                    on_will_accept=lambda e, i=idx: on_will_accept(e, i),
                    on_accept=lambda e, i=idx: on_accept(e, i),
                )
                
                images_grid.controls.append(img_target)
            except Exception as e:
                print(f"Error al cargar la imagen {img_path}: {e}")
        
        page.update()
    
    # Función para eliminar una imagen de la lista
    def remove_image(idx):
        selected_images.pop(idx)
        update_image_list()
        convert_button.disabled = len(selected_images) == 0
        page.update()
    
    # Función para limpiar todas las imágenes seleccionadas
    def clear_all(e):
        selected_images.clear()
        update_image_list()
        convert_button.disabled = True
        page.update()
    
    # Función para convertir las imágenes a PDF
    def convert_to_pdf(e):
        if not selected_images:
            return
        
        # Cambiar el estado del botón de conversión y mostrar el progreso
        convert_button.disabled = True
        progress_bar.visible = True
        status_text.value = "Convirtiendo imágenes a PDF..."
        page.update()
        
        try:
            # Generar nombre de archivo basado en la fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"ImagenesToPDF_{timestamp}.pdf"
            
            # Abre el diálogo para guardar el archivo
            save_file_dialog.save_file(
                initial_file_name=output_filename,
                allowed_extensions=["pdf"]
            )
        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            convert_button.disabled = False
            progress_bar.visible = False
            page.update()
    
    # Función para procesar el resultado del diálogo de guardar
    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                # Crear una lista para almacenar las imágenes abiertas
                images = []
                
                # Abrir la primera imagen para usar como base
                first_image = Image.open(selected_images[0])
                first_image = first_image.convert('RGB')
                
                # Abrir las imágenes restantes
                if len(selected_images) > 1:
                    for img_path in selected_images[1:]:
                        img = Image.open(img_path)
                        # Convertir a RGB para asegurar compatibilidad con PDF
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        images.append(img)
                
                # Guardar todas las imágenes como un PDF
                first_image.save(
                    e.path,
                    save_all=True,
                    append_images=images,
                    quality=95
                )
                
                status_text.value = f"PDF creado exitosamente: {os.path.basename(e.path)}"
            except Exception as ex:
                status_text.value = f"Error al guardar el PDF: {str(ex)}"
            finally:
                convert_button.disabled = False
                progress_bar.visible = False
                page.update()
    
    # Crear el diálogo para guardar el archivo
    save_file_dialog = ft.FilePicker(on_result=save_file_result)
    page.overlay.append(save_file_dialog)
    
    # Elementos de la interfaz de usuario
    title = ft.Text("Convertidor de Imágenes a PDF", size=32, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text("Selecciona imágenes para convertir a un archivo PDF", size=16)
    drag_info = ft.Text("Arrastra las imágenes para reordenarlas", size=14, italic=True, color=ft.colors.BLUE)
    
    select_button = ft.ElevatedButton(
        "Seleccionar imágenes",
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: pick_files_dialog.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.IMAGE
        )
    )
    
    clear_button = ft.OutlinedButton(
        "Limpiar todo",
        icon=ft.icons.CLEAR_ALL,
        on_click=clear_all
    )
    
    convert_button = ft.ElevatedButton(
        "Convertir a PDF",
        icon=ft.icons.PICTURE_AS_PDF,
        on_click=convert_to_pdf,
        disabled=True,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.GREEN_700,
        )
    )
    
    # Contenedor para mostrar la lista de imágenes
    images_grid = ft.GridView(
        runs_count=5,
        max_extent=200,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
        padding=10,
        expand=True
    )
    # prueba
    
    # Barra de progreso (inicialmente oculta)
    progress_bar = ft.ProgressBar(width=400, visible=False)
    
    # Texto de estado
    status_text = ft.Text("", size=14)
     
    # Construir la interfaz
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Row([title], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([subtitle], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([drag_info], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(),
                    ft.Row(
                        [select_button, clear_button, convert_button],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=images_grid,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=10,
                        padding=5,
                        margin=10,
                        expand=True
                    ),
                    ft.Row([progress_bar], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=10,
                expand=True
            ),
            padding=20,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main)