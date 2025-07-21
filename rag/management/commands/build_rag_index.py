from django.core.management.base import BaseCommand, CommandError
from ...helpers import rag_helper


class Command(BaseCommand):
    help = 'Builds or rebuilds the FAISS RAG index from the GoogleSheetData table.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting RAG index build process..."))

        try:
            success = rag_helper.build_and_save_faiss_index(logger=self.stdout.write)
            if success:
                self.stdout.write(self.style.SUCCESS("RAG index built and saved successfully."))
            else:
                self.stdout.write(
                    self.style.WARNING("RAG index build completed, but no data was indexed (possibly empty table)."))
        except Exception as e:
            raise CommandError(f"Error building RAG index: {e}")