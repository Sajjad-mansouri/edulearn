document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname.replace(/\/$/, "");

    const links = [...document.querySelectorAll(".sidebar-link[data-nav]")];

    const matchingLinks = links.filter(link => {
        const navPath = link.dataset.nav.replace(/\/$/, "");


        return (
            currentPath === navPath ||
            currentPath.startsWith(`${navPath}/`)
        );
    });

    // Only the most specific route becomes active
    const activeLink = matchingLinks.reduce((best, link) => {
        if (!best) return link;

        return link.dataset.nav.length > best.dataset.nav.length
            ? link
            : best;
    }, null);

    if (activeLink) {
        activeLink.classList.add("active");
    }
});
