import streamlit as st
import re

# Page config
st.set_page_config(
    page_title="STL Tags Converter",
    layout="wide"
)

# Mapping from old tag names/types to new theme_prop names
TAG_MAPPING = {
    'CMResultsAdUrl_font-size': 'ad_url_font_size',
    'CMResultsAdUrl_color': 'ad_url_font_color',
    'CMResultsAdUrl_font-family': 'ad_url_font-family',
    'CMResultsAdTitle_font-size': 'ad_title_font_size',
    'CMResultsAdTitle_color': 'ad_title_color',
    'CMResultsAdTitle_font-family': 'ad_title_font_family',
    'CMResultsAdDescription_font-size': 'ad_desc_font_size',
    'CMResultsAdDescription_color': 'ad_desc_font_color',
    'CMResultsAdDescription_font-family': 'ad_desc_font_family',
    'ResultsAdDescription_font-size': 'ad_desc_desktop_font_size',
    'CustomResultsAdUrlBackGround_color': 'ad_background',
    'CustomResultsAdUrlBorder_color': 'ad_border_color',
    'CMContentArea_color': 'body_background',
    'HeaderArea_color': 'header_background',
    'AdBorder_color': 'cta_border_color',
    'CMAdsLabel_color': 'cta_background',
    'Bullet_font-size': 'cta_text_font_size',
    'BulletText_color': 'cta_text_font_color',
    'BulletShape_color': 'chevron_color',
    'KeywordsHoverUnderline_checkbox': 'title_hover_underline',
    'KeywordArea_color': 'keyword_link_color',
    'relcontspan_font-family': 'relcont_span_font_family',
    'HeaderText_font-size': 'header_text_font_size',
    'HeaderText_color': 'header_text_color',
    'HeaderText_textCase': 'header_text_case',
    'HeaderText_tallness': 'header_border_width',
    'HeaderText_border-style': 'header_border_style',
    'CMResultsAdUrl_font-size_desktop': 'ad_url_desktop_font_size',
    'CMResultsAdTitle_font-size_desktop': 'ad_title_desktop_font_size',
    'AdBorder_color_desktop': 'cta_border_desktop_color',
    'InnerBorder_color': 'ad_url_font_color',
    'CallToAction_content': 'cta_text'
}

def convert_tag(match, name, value, type):
    """Convert old tag format to new theme_prop format"""
    key = f"{name}_{type}"
    new_prop_name = TAG_MAPPING.get(key)
    
    # If no mapping found, create a default name
    if not new_prop_name:
        # Convert CamelCase to snake_case
        new_prop_name = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_').replace('__', '_') + '_' + type.lower()
    
    return f'<tag:theme_prop:{new_prop_name} default="{value}" />'

def convert_tags(input_html):
    """Main conversion function"""
    if not input_html or not input_html.strip():
        return ""
    
    output = input_html
    
    # Convert <tagd:style name="..." value="..." type="..." /> to <tag:theme_prop:... default="..." />
    output = re.sub(
        r'<tagd:style\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s+type=["\']([^"\']+)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(1), m.group(2), m.group(3)),
        output,
        flags=re.IGNORECASE
    )
    
    # Also handle tags with different attribute order
    output = re.sub(
        r'<tagd:style\s+type=["\']([^"\']+)["\']\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(2), m.group(3), m.group(1)),
        output,
        flags=re.IGNORECASE
    )
    
    # Clean up: ensure tags don't have excessive line breaks around them
    output = re.sub(r'\s*\n\s*(<tag:[^>]+>)\s*\n\s*', r' \1 ', output)
    output = re.sub(r'(<tag:[^>]+>)\s*\n\s*', r'\1 ', output)
    
    return output

# UI
st.title("STL Tags Converter")
st.markdown("**Convert Old Framework Tags to New Framework Format**")
st.markdown("---")

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Old Framework (Input)")
    
    input_text = st.text_area(
        "Paste your old framework HTML here:",
        value="",
        height=600,
        key="input",
        label_visibility="collapsed"
    )
    
    # Convert button
    if st.button("Convert", key="convert", use_container_width=True):
        st.rerun()

with col2:
    st.subheader("New Framework (Output)")
    
    # Always show output textarea
    if input_text:
        output_text = convert_tags(input_text)
        
        # Count conversions
        old_tag_count = len(re.findall(r'<tagd:style', input_text, re.IGNORECASE))
        new_tag_count = len(re.findall(r'<tag:theme_prop:', output_text, re.IGNORECASE))
        
        # Display stats
        if old_tag_count > 0:
            st.success(f"Converted {old_tag_count} tags → {new_tag_count} new tags")
    else:
        output_text = ""
    
    output_area = st.text_area(
        "Converted HTML:",
        value=output_text,
        height=600,
        key="output",
        label_visibility="collapsed",
        placeholder="Converted HTML will appear here..."
    )
    
    # Download button
    if output_text:
        st.download_button(
            label="Download Converted HTML",
            data=output_text,
            file_name="converted_framework.html",
            mime="text/html"
        )

# Footer
st.markdown("---")
st.caption("Made with Streamlit")
