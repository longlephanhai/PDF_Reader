import pymupdf as fitz
import json
import os


class PDFModel:
    def __init__(self):
        self.doc = None
        self.file_path = None
        self.current_page = 0
        self.search_results = []
        self.current_search_index = -1
        self.last_search_text = ""
        self.bookmarks_file = "pdf_bookmarks.json"
        self.bookmarks = self.load_bookmarks()

    def load_pdf(self, path):
        self.doc = fitz.open(path)
        self.file_path = path
        self.current_page = self.get_bookmark(path)
        self.clear_search()

    def get_page_count(self):
        return len(self.doc) if self.doc else 0

    def get_current_page_pixmap(self, zoom=1.0):
        if not self.doc:
            return None
        page = self.doc[self.current_page]
        mat = fitz.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, annots=True)

    def get_pixmap_by_index(self, idx, zoom=1.0):
        if not self.doc or not (0 <= idx < len(self.doc)):
            return None
        page = self.doc[idx]
        mat = fitz.Matrix(zoom, zoom)
        return page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, annots=True)

    def get_current_page(self):
        if not self.doc:
            return None
        return self.doc[self.current_page]

    def get_page_by_index(self, idx):
        if not self.doc or not (0 <= idx < len(self.doc)):
            return None
        return self.doc[idx]

    #  Navigation
    def next_page(self):
        if self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.save_bookmark(self.file_path, self.current_page)
            return True
        return False

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.save_bookmark(self.file_path, self.current_page)
            return True
        return False

    def go_to_page(self, num):
        if 1 <= num <= len(self.doc):
            self.current_page = num - 1
            self.save_bookmark(self.file_path, self.current_page)
            return True
        return False

    #  Bookmark Management
    def load_bookmarks(self):
        if os.path.exists(self.bookmarks_file):
            try:
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading bookmarks: {e}")
                return {}
        return {}

    def save_bookmark(self, file_path, page_num):
        if not file_path:
            return False

        try:
            self.bookmarks[file_path] = page_num
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving bookmark: {e}")
            return False

    def get_bookmark(self, file_path):

        return self.bookmarks.get(file_path, 0)

    #  Page Rotation
    def rotate_current_page(self, rotation=90):
        if not self.doc:
            return False

        try:
            page = self.doc[self.current_page]
            page.set_rotation(rotation)
            return True
        except Exception as e:
            print(f"Error rotating page: {e}")
            return False

    def rotate_page_by_index(self, idx, rotation=90):
        if not self.doc or not (0 <= idx < len(self.doc)):
            return False

        try:
            page = self.doc[idx]
            page.set_rotation(rotation)
            return True
        except Exception as e:
            print(f"Error rotating page: {e}")
            return False

    def rotate_all_pages(self, rotation=90):
        if not self.doc:
            return False

        try:
            for page in self.doc:
                page.set_rotation(rotation)
            return True
        except Exception as e:
            print(f"Error rotating all pages: {e}")
            return False

    def get_page_rotation(self, idx=None):
        if not self.doc:
            return 0

        try:
            if idx is None:
                idx = self.current_page
            if 0 <= idx < len(self.doc):
                return self.doc[idx].rotation
        except Exception as e:
            print(f"Error getting rotation: {e}")
        return 0

    #  Page Operations
    def delete_current_page(self):
        if self.doc and len(self.doc) > 1:
            self.doc.delete_page(self.current_page)
            if self.current_page >= len(self.doc):
                self.current_page = len(self.doc) - 1
            return True
        return False

    def delete_pages(self, indices):
        if not self.doc:
            return False
        for i in sorted(set(indices), reverse=True):
            if 0 <= i < len(self.doc):
                self.doc.delete_page(i)
        if self.current_page >= len(self.doc):
            self.current_page = max(0, len(self.doc) - 1)
        return True

    def add_new_page(self, position=-1):
        if not self.doc:
            return False

        try:
            if position == -1:
                self.doc.new_page()
            else:
                self.doc.new_page(pno=position)
            return True
        except Exception as e:
            print(f"Error adding page: {e}")
            return False

    def insert_page_after_current(self):
        if not self.doc:
            return False

        try:
            self.doc.new_page(pno=self.current_page + 1)
            self.current_page += 1
            return True
        except Exception as e:
            print(f"Error inserting page: {e}")
            return False

    def insert_page_before_current(self):
        if not self.doc:
            return False

        try:
            self.doc.new_page(pno=self.current_page)
            return True
        except Exception as e:
            print(f"Error inserting page: {e}")
            return False

    #  Annotation Operations
    def add_highlight_annotation(self, rect, color=(1, 1, 0), opacity=0.4):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            annot = page.add_rect_annot(rect)
            annot.set_colors(stroke=None, fill=color)
            annot.set_opacity(opacity)
            annot.update()
            return annot
        except Exception as e:
            print(f"Error adding highlight: {e}")
            return None

    def add_underline_annotation(self, rect, color=(0, 0, 1)):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            annot = page.add_underline_annot(rect)
            annot.set_colors(stroke=color)
            annot.update()
            return annot
        except Exception as e:
            print(f"Error adding underline: {e}")
            return None

    def add_strikeout_annotation(self, rect, color=(1, 0, 0)):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            annot = page.add_strikeout_annot(rect)
            annot.set_colors(stroke=color)
            annot.update()
            return annot
        except Exception as e:
            print(f"Error adding strikeout: {e}")
            return None

    def add_text_annotation(self, rect, text, icon="Note", color=(1, 0.8, 0), opacity=0.9):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            point = fitz.Point(rect.x1 - 20, rect.y1 - 10)
            annot = page.add_text_annot(point, text, icon=icon)
            annot.set_colors(stroke=color)
            annot.set_opacity(opacity)
            annot.update()
            return annot
        except Exception as e:
            print(f"Error adding text annotation: {e}")
            return None

    def add_freetext(self, rect, text, fontsize=12, color=(0, 0, 0), bg_color=(1, 1, 1), border_width=1):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            annot = page.add_freetext_annot(
                rect,
                text,
                fontsize=fontsize,
                text_color=color,
                fill_color=bg_color
            )
            if border_width > 0:
                annot.set_border(width=border_width)
            else:
                annot.set_border(width=0)
            annot.update()
            return annot
        except Exception as e:
            print(f"Error adding freetext: {e}")
            return None

    def remove_text_in_rect(self, rect, color=(1, 1, 1)):
        if not self.doc:
            return None

        page = self.doc[self.current_page]
        try:
            annot = page.add_redact_annot(rect, fill=color)
            annot.update()
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            return annot
        except Exception as e:
            print(f"Error removing text (trying fallback method): {e}")
            try:
                # Method 2: Fallback - cover with white rectangle
                annot = page.add_rect_annot(rect)
                annot.set_colors(stroke=color, fill=color)
                annot.set_opacity(1.0)
                annot.update()
                return annot
            except Exception as e2:
                print(f"Error in fallback method: {e2}")
                return None

    #  Erase Annotation Operations
    def erase_annotations_in_rect(self, rect):
        if not self.doc:
            return 0

        page = self.doc[self.current_page]
        removed_count = 0

        try:
            annot = page.first_annot
            while annot:
                next_annot = annot.next

                annot_rect = annot.rect
                if annot_rect.intersects(rect) or rect.intersects(annot_rect):
                    try:
                        page.delete_annot(annot)
                        removed_count += 1
                    except Exception as e:
                        print(f"Error deleting annotation: {e}")

                annot = next_annot

            if removed_count > 0:
                page.update()

        except Exception as e:
            print(f"Error in erase_annotations_in_rect: {e}")

        return removed_count

    def erase_annotation_at_point(self, point):
        if not self.doc:
            return False

        page = self.doc[self.current_page]

        try:
            annot = page.first_annot
            while annot:
                next_annot = annot.next
                rect = annot.rect

                if rect.contains(point):
                    page.delete_annot(annot)
                    page.update()
                    return True

                annot = next_annot

        except Exception as e:
            print(f"Error deleting annotation at point: {e}")

        return False

    def erase_annotation(self, point=None, rect=None):
        if rect:
            return self.erase_annotations_in_rect(rect) > 0
        elif point:
            return self.erase_annotation_at_point(point)
        return False

    def get_annotations_in_rect(self, rect):
        if not self.doc:
            return []

        page = self.doc[self.current_page]
        annotations = []

        try:
            annot = page.first_annot
            while annot:
                annot_rect = annot.rect
                if annot_rect.intersects(rect) or rect.intersects(annot_rect):
                    annotations.append({
                        'type': annot.type,
                        'rect': annot_rect,
                        'info': annot.info
                    })
                annot = annot.next
        except Exception as e:
            print(f"Error getting annotations: {e}")

        return annotations

    def clear_all_annotations_on_page(self):
        if not self.doc:
            return 0

        page = self.doc[self.current_page]
        removed_count = 0

        try:
            annot = page.first_annot
            while annot:
                next_annot = annot.next
                try:
                    page.delete_annot(annot)
                    removed_count += 1
                except:
                    pass
                annot = next_annot

            if removed_count > 0:
                page.update()

        except Exception as e:
            print(f"Error clearing all annotations: {e}")

        return removed_count

    #  Text Extraction
    def get_text_regions(self):
        if not self.doc:
            return [], None

        page = self.doc[self.current_page]
        try:
            textpage = page.get_textpage()
            blocks = textpage.extractBLOCKS()
            text_rects = [fitz.Rect(b[:4]) for b in blocks if len(b) >= 5]
            return text_rects, page.rect
        except Exception as e:
            print(f"Error extracting text regions: {e}")
            return [], None

    #  Search Operations
    def search_text(self, search_text):
        if not self.doc:
            return []

        self.clear_search()
        self.last_search_text = search_text

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            try:
                instances = page.search_for(search_text)
                for rect in instances:
                    self.search_results.append({
                        'page': page_num,
                        'rect': rect,
                        'text': search_text,
                        'annot': None
                    })
            except Exception as e:
                print(f"Error searching page {page_num}: {e}")

        if self.search_results:
            self.current_search_index = 0

        return self.search_results

    def get_search_result_count(self):
        return len(self.search_results)

    def get_current_search_match(self):
        if 0 <= self.current_search_index < len(self.search_results):
            return self.search_results[self.current_search_index]
        return None

    def next_search_result(self):
        if not self.search_results:
            return None

        if 0 <= self.current_search_index < len(self.search_results):
            old_match = self.search_results[self.current_search_index]
            self._delete_annotation(old_match)

        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        return self.search_results[self.current_search_index]

    def prev_search_result(self):
        if not self.search_results:
            return None

        if 0 <= self.current_search_index < len(self.search_results):
            old_match = self.search_results[self.current_search_index]
            self._delete_annotation(old_match)

        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        return self.search_results[self.current_search_index]

    def highlight_search_match(self, match):
        if not match or match['page'] >= len(self.doc):
            return None

        page = self.doc[match['page']]
        try:
            if match.get('annot'):
                self._delete_annotation(match)

            annot = page.add_highlight_annot(match['rect'])
            annot.set_colors(fill=(0, 1, 0))
            annot.set_opacity(0.4)
            annot.update()

            match['annot'] = annot
            return annot
        except Exception as e:
            print(f"Error highlighting match: {e}")
            return None

    def clear_search_highlights(self):
        for match in self.search_results:
            self._delete_annotation(match)

    def clear_search(self):
        self.clear_search_highlights()
        self.search_results = []
        self.current_search_index = -1
        self.last_search_text = ""

    def _delete_annotation(self, match):
        if match.get('annot'):
            try:
                page = self.doc[match['page']]
                page.delete_annot(match['annot'])
                match['annot'] = None
            except:
                pass

    def save(self):
        if not self.doc or not self.file_path:
            return False
        try:
            self.doc.save(self.file_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            print(f"Saved to: {self.file_path}")
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False

    def save_as(self, new_path):
        if not self.doc or not new_path:
            return False

        if not new_path.lower().endswith(".pdf"):
            new_path += ".pdf"

        try:
            self.doc.save(new_path, garbage=4, deflate=True, clean=True)
            self.file_path = new_path
            print(f"Saved to: {new_path}")
            return True
        except Exception as e:
            print(f"Error saving as: {e}")
            return False

    #  Export to PDF (specific pages)
    def export_pages(self, page_indices, output_path):
        if not self.doc or not page_indices:
            return False

        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        try:
            new_doc = fitz.open()
            for idx in sorted(set(page_indices)):
                if 0 <= idx < len(self.doc):
                    new_doc.insert_pdf(self.doc, from_page=idx, to_page=idx)

            new_doc.save(output_path, garbage=4, deflate=True, clean=True)
            new_doc.close()
            print(f"Exported {len(page_indices)} pages to: {output_path}")
            return True
        except Exception as e:
            print(f"Error exporting pages: {e}")
            return False

    def export_current_page(self, output_path):
        return self.export_pages([self.current_page], output_path)

    def export_page_range(self, start_page, end_page, output_path):
        if not self.doc:
            return False

        if not (0 <= start_page < len(self.doc) and 0 <= end_page < len(self.doc)):
            return False

        page_indices = list(range(start_page, end_page + 1))
        return self.export_pages(page_indices, output_path)

    def extract_text_from_rect(self, rect):
        if not self.doc:
            return ""

        page = self.doc[self.current_page]
        try:
            text = page.get_text("text", clip=rect)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def get_selected_text(self, rect):

        return self.extract_text_from_rect(rect)

    def extract_text_from_page(self, page_num):
        if not self.doc or not (0 <= page_num < len(self.doc)):
            return ""

        try:
            page = self.doc[page_num]
            text = page.get_text("text")
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from page {page_num}: {e}")
            return ""

    def extract_text_from_pages(self, page_indices):
        if not self.doc:
            return ""

        all_text = []
        for idx in page_indices:
            if 0 <= idx < len(self.doc):
                text = self.extract_text_from_page(idx)
                if text:
                    all_text.append(f"--- Page {idx + 1} ---\n{text}")

        return "\n\n".join(all_text)

    def extract_text_from_all_pages(self):
        if not self.doc:
            return ""

        page_indices = list(range(len(self.doc)))
        return self.extract_text_from_pages(page_indices)