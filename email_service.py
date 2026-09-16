import smtplib

from email.message import EmailMessage

from config import (
    EMAIL,
    EMAIL_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
    SITE_URL
)


class EmailService:

    @staticmethod
    def send_email(destination, subject, body):

        msg = EmailMessage()

        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = destination

        msg.set_content(body)

        server = smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.login(
            EMAIL,
            EMAIL_PASSWORD
        )

        server.send_message(msg)

        server.quit()

    # ----------------------------------------------------
    # FOTO RECIBIDA
    # ----------------------------------------------------

    @staticmethod
    def send_submission_email(photo):

        link = f"{SITE_URL}/edit/{photo.token}"

        body = f"""
Hola {photo.photographer.first_name},

Recibimos correctamente tu fotografía.

Actualmente se encuentra en estado:

PENDIENTE DE REVISIÓN

Puedes modificar la información antes de que sea aprobada desde:

{link}

Gracias por formar parte de AstroLab.
"""

        EmailService.send_email(

            photo.photographer.email,

            "AstroLab | Fotografía recibida",

            body

        )

    # ----------------------------------------------------
    # FOTO APROBADA
    # ----------------------------------------------------

    @staticmethod
    def send_approved_email(photo):

        body = f"""
Hola {photo.photographer.first_name},

Nos alegra informarte que tu fotografía

"{photo.title}"

ha sido aprobada.

Ya forma parte de la galería pública de AstroLab.

¡Muchas gracias por compartir tu trabajo!
"""

        EmailService.send_email(

            photo.photographer.email,

            "AstroLab | Fotografía aprobada",

            body

        )

    # ----------------------------------------------------
    # FOTO RECHAZADA
    # ----------------------------------------------------

    @staticmethod
    def send_rejected_email(photo):

        body = f"""
Hola {photo.photographer.first_name},

Tu fotografía

"{photo.title}"

no pudo ser publicada.

Motivo:

{photo.reject_reason}

Puedes corregirla desde el enlace recibido anteriormente y volver a enviarla.

Gracias por colaborar con AstroLab.
"""

        EmailService.send_email(

            photo.photographer.email,

            "AstroLab | Revisión de fotografía",

            body

        )

    # ----------------------------------------------------
    # ELIMINACIÓN
    # ----------------------------------------------------

    @staticmethod
    def send_deleted_email(photo):

        body = f"""
Hola {photo.photographer.first_name},

Tu fotografía

"{photo.title}"

ha sido eliminada de AstroLab.

Si crees que se trata de un error puedes comunicarte con el administrador.

Saludos.
"""

        EmailService.send_email(

            photo.photographer.email,

            "AstroLab | Fotografía eliminada",

            body

        )

    # ----------------------------------------------------
    # SOLICITUD DE CAMBIOS
    # ----------------------------------------------------

    @staticmethod
    def send_changes_requested(photo):

        link = f"{SITE_URL}/edit/{photo.token}"

        body = f"""
Hola {photo.photographer.first_name},

Antes de publicar tu fotografía necesitamos que realices algunos cambios.

Motivo:

{photo.reject_reason}

Puedes editar toda la información desde:

{link}

Una vez guardados los cambios volverá automáticamente a estado Pendiente.

Gracias.
"""

        EmailService.send_email(

            photo.photographer.email,

            "AstroLab | Solicitud de cambios",

            body

        )